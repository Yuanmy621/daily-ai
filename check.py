#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SCHEMA_FIELDS = {
    "raw": {
        "required": ["id", "title", "source", "published_at", "raw_content"],
        "text_field": "raw_content",
    },
    "normalized": {
        "required": ["id", "title", "source", "published_at", "content"],
        "text_field": "content",
    },
    "structured": {
        "required": [
            "id",
            "title",
            "source",
            "published_at",
            "language",
            "summary",
            "entities",
            "topic",
            "event_type",
            "region",
            "importance_score",
            "sentiment",
            "risk_signals",
            "opportunity_signals",
            "evidence",
        ],
        "text_field": "summary",
    },
}

FIELD_TYPES = {
    "id": str,
    "title": str,
    "source": str,
    "published_at": str,
    "url": str,
    "language": str,
    "raw_content": str,
    "content": str,
    "summary": str,
    "topic": str,
    "event_type": str,
    "region": str,
    "sentiment": str,
    "importance_score": (int, float),
    "entities": list,
    "risk_signals": list,
    "opportunity_signals": list,
    "evidence": list,
}

AI_KEYWORDS = {
    "ai",
    "artificial intelligence",
    "llm",
    "model",
    "models",
    "agent",
    "agents",
    "openai",
    "anthropic",
    "claude",
    "gemini",
    "gpt",
    "deepseek",
    "chatgpt",
    "multimodal",
    "machine learning",
    "机器学习",
    "人工智能",
    "大模型",
    "模型",
    "智能体",
    "生成式",
    "多模态",
    "推理模型",
}

CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?$")


@dataclass
class Issue:
    level: str
    check: str
    message: str
    file: str
    record_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "level": self.level,
            "check": self.check,
            "message": self.message,
            "file": self.file,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check scraped news content quality.")
    parser.add_argument("input_path", help="JSON/JSONL file or directory to validate")
    parser.add_argument(
        "--schema",
        choices=sorted(SCHEMA_FIELDS.keys()),
        default="normalized",
        help="Schema to validate against (default: normalized)",
    )
    parser.add_argument("--report", help="Write JSON report to this path")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well")
    parser.add_argument("--min-count", type=int, default=5, help="Minimum expected record count")
    parser.add_argument("--max-count", type=int, default=100, help="Maximum expected record count")
    parser.add_argument("--max-age-days", type=int, default=7, help="Warn if records are older than this")
    parser.add_argument("--quiet", action="store_true", help="Only print final PASS/FAIL result")
    return parser.parse_args()


def parse_datetime(value: str) -> datetime | None:
    if not isinstance(value, str) or not value.strip() or not ISO_DATE_RE.match(value.strip()):
        return None

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iter_input_files(input_path: Path) -> list[Path]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input path not found: {input_path}")

    if input_path.is_file():
        return [input_path]

    files = sorted(
        path
        for path in input_path.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl"}
    )
    if not files:
        raise FileNotFoundError(f"No .json or .jsonl files found under: {input_path}")
    return files


def _ensure_record_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        records = []
        for index, item in enumerate(payload):
            if not isinstance(item, dict):
                raise ValueError(f"JSON array item at index {index} is not an object")
            records.append(item)
        return records

    if isinstance(payload, dict):
        if 'articles' in payload:
            articles = payload['articles']
            if not isinstance(articles, list):
                raise ValueError("field articles must be a list")
            records = []
            for index, item in enumerate(articles):
                if not isinstance(item, dict):
                    raise ValueError(f"articles item at index {index} is not an object")
                records.append(item)
            return records
        return [payload]

    raise ValueError("Top-level JSON must be an object, array, or JSONL object stream")


def load_records(file_path: Path) -> list[dict[str, Any]]:
    text = file_path.read_text(encoding="utf-8")
    if not text.strip():
        return []

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}: {exc.msg}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"JSONL line {line_number} is not an object")
            records.append(item)
        return records

    return _ensure_record_list(payload)


def add_issue(
    issues: list[Issue],
    level: str,
    check: str,
    message: str,
    file_path: Path,
    record_id: str | None = None,
) -> None:
    issues.append(
        Issue(
            level=level,
            check=check,
            message=message,
            file=str(file_path),
            record_id=record_id,
        )
    )


def is_blank_string(value: Any) -> bool:
    return isinstance(value, str) and not value.strip()


def looks_like_ai_news(title: str, text: str) -> bool:
    haystack = f"{title} {text}".lower()
    return any(keyword in haystack for keyword in AI_KEYWORDS)


def invalid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme not in {"http", "https"} or not parsed.netloc


def has_garbled_text(text: str) -> bool:
    if not text:
        return False
    bad_chars = text.count("�")
    control_chars = len(CONTROL_CHAR_RE.findall(text))
    return (bad_chars + control_chars) / max(len(text), 1) > 0.01


def validate_record(
    record: dict[str, Any],
    schema_name: str,
    file_path: Path,
    max_age_days: int,
) -> list[Issue]:
    issues: list[Issue] = []
    schema = SCHEMA_FIELDS[schema_name]
    record_id = record.get("id") if isinstance(record.get("id"), str) else None
    text_field = schema["text_field"]

    for field in schema["required"]:
        if field not in record:
            add_issue(issues, "ERROR", "missing_field", f"missing required field: {field}", file_path, record_id)
            continue
        expected_type = FIELD_TYPES.get(field)
        value = record[field]
        if expected_type and not isinstance(value, expected_type):
            add_issue(
                issues,
                "ERROR",
                "field_type",
                f"field {field} has invalid type: expected {type_name(expected_type)}",
                file_path,
                record_id,
            )

    for field in ("id", "title", "source", "published_at", "language", text_field):
        if field in record and is_blank_string(record[field]):
            add_issue(issues, "ERROR", "blank_field", f"field {field} is blank", file_path, record_id)

    published_at = record.get("published_at")
    dt = parse_datetime(published_at) if isinstance(published_at, str) else None
    if "published_at" in record and dt is None:
        add_issue(issues, "ERROR", "invalid_datetime", "published_at is not a valid ISO datetime", file_path, record_id)
    elif dt is not None:
        if dt < datetime.now(timezone.utc) - timedelta(days=max_age_days):
            add_issue(
                issues,
                "WARNING",
                "stale_datetime",
                f"published_at is older than {max_age_days} days",
                file_path,
                record_id,
            )

    title = record.get("title") if isinstance(record.get("title"), str) else ""
    text_value = record.get(text_field) if isinstance(record.get(text_field), str) else ""

    if title and len(title.strip()) < 10:
        add_issue(issues, "WARNING", "short_title", "title is shorter than 10 characters", file_path, record_id)

    if text_value:
        if len(text_value.strip()) < 50:
            add_issue(issues, "WARNING", "short_text", f"{text_field} is shorter than 50 characters", file_path, record_id)
        if len(text_value) > 50000:
            add_issue(issues, "WARNING", "long_text", f"{text_field} is longer than 50000 characters", file_path, record_id)
        if title.strip() and title.strip() == text_value.strip():
            add_issue(issues, "WARNING", "duplicated_title_text", f"title is identical to {text_field}", file_path, record_id)
        if has_garbled_text(text_value):
            add_issue(issues, "INFO", "garbled_text", f"{text_field} may contain garbled characters", file_path, record_id)

    url = record.get("url")
    if isinstance(url, str) and url.strip() and invalid_url(url.strip()):
        add_issue(issues, "WARNING", "invalid_url", "url is not a valid http/https URL", file_path, record_id)

    if schema_name == "structured":
        importance = record.get("importance_score")
        if isinstance(importance, (int, float)) and not (0 <= float(importance) <= 10):
            add_issue(
                issues,
                "ERROR",
                "importance_range",
                "importance_score must be between 0 and 10",
                file_path,
                record_id,
            )
        evidence = record.get("evidence")
        if isinstance(evidence, list):
            if not evidence or not all(isinstance(item, str) and item.strip() for item in evidence):
                add_issue(issues, "ERROR", "invalid_evidence", "evidence must be a non-empty list of non-blank strings", file_path, record_id)
        for list_field in ("entities", "risk_signals", "opportunity_signals", "evidence"):
            value = record.get(list_field)
            if isinstance(value, list) and not all(isinstance(item, str) for item in value):
                add_issue(issues, "ERROR", "list_item_type", f"{list_field} must contain only strings", file_path, record_id)
    else:
        if title or text_value:
            if not looks_like_ai_news(title, text_value):
                add_issue(issues, "INFO", "non_ai_related", "record may not be AI-related", file_path, record_id)

    return issues


def type_name(expected_type: Any) -> str:
    if isinstance(expected_type, tuple):
        return " or ".join(tp.__name__ for tp in expected_type)
    return expected_type.__name__


def validate_dataset(
    files: list[Path],
    schema_name: str,
    min_count: int,
    max_count: int,
    max_age_days: int,
) -> tuple[list[Issue], int]:
    issues: list[Issue] = []
    total_records = 0
    ids: list[tuple[str, Path]] = []
    urls: list[tuple[str, Path, str | None]] = []
    titles: list[tuple[str, Path, str | None]] = []

    for file_path in files:
        try:
            records = load_records(file_path)
        except (OSError, UnicodeDecodeError) as exc:
            add_issue(issues, "ERROR", "file_read", str(exc), file_path)
            continue
        except ValueError as exc:
            add_issue(issues, "ERROR", "json_parse", str(exc), file_path)
            continue

        if not records:
            add_issue(issues, "WARNING", "empty_file", "file contains no records", file_path)
            continue

        for record in records:
            total_records += 1
            if not isinstance(record, dict):
                add_issue(issues, "ERROR", "record_type", "record is not an object", file_path)
                continue
            record_id = record.get("id") if isinstance(record.get("id"), str) else None
            if record_id:
                ids.append((record_id, file_path))
            if isinstance(record.get("url"), str) and record["url"].strip():
                urls.append((record["url"].strip(), file_path, record_id))
            if isinstance(record.get("title"), str) and record["title"].strip():
                titles.append((record["title"].strip(), file_path, record_id))
            issues.extend(validate_record(record, schema_name, file_path, max_age_days))

    if total_records < min_count:
        add_issue(
            issues,
            "WARNING",
            "low_count",
            f"record count {total_records} is below min-count {min_count}",
            files[0],
        )
    if total_records > max_count:
        add_issue(
            issues,
            "WARNING",
            "high_count",
            f"record count {total_records} exceeds max-count {max_count}",
            files[0],
        )

    issues.extend(find_duplicates(ids, "duplicate_id", "ERROR"))
    issues.extend(find_duplicates(urls, "duplicate_url", "WARNING"))
    issues.extend(find_duplicates(titles, "duplicate_title", "WARNING"))

    return issues, total_records


def find_duplicates(entries: list[tuple[Any, Path, str | None] | tuple[Any, Path]], check: str, level: str) -> list[Issue]:
    issues: list[Issue] = []
    counter = Counter(entry[0] for entry in entries)
    duplicates = {value for value, count in counter.items() if count > 1}
    for entry in entries:
        value = entry[0]
        if value not in duplicates:
            continue
        file_path = entry[1]
        record_id = entry[2] if len(entry) > 2 else None
        issues.append(
            Issue(
                level=level,
                check=check,
                message=f"duplicate value detected: {value}",
                file=str(file_path),
                record_id=record_id,
            )
        )
    return issues


def build_summary(issues: list[Issue]) -> dict[str, int]:
    counter = Counter(issue.level for issue in issues)
    return {
        "ERROR": counter.get("ERROR", 0),
        "WARNING": counter.get("WARNING", 0),
        "INFO": counter.get("INFO", 0),
    }


def overall_result(summary: dict[str, int], strict: bool) -> str:
    if summary["ERROR"] > 0:
        return "FAIL"
    if strict and summary["WARNING"] > 0:
        return "FAIL"
    return "PASS"


def print_report(
    input_path: Path,
    schema_name: str,
    files: list[Path],
    total_records: int,
    summary: dict[str, int],
    result: str,
    issues: list[Issue],
    quiet: bool,
) -> None:
    if quiet:
        print(result)
        return

    print(f"[check.py] Checking {total_records} records from {len(files)} file(s) as schema={schema_name}")
    print(f"Summary: {summary['ERROR']} ERROR(s), {summary['WARNING']} WARNING(s), {summary['INFO']} INFO(s)")
    print(f"Result: {result}")

    if issues:
        print("Issues:")
        for issue in issues:
            location = issue.record_id or "<unknown-id>"
            print(f"  - [{issue.level}] {issue.check} {location}: {issue.message} ({issue.file})")
    else:
        print("Issues: none")

    print(f"Input: {input_path}")


def write_json_report(
    report_path: Path,
    input_path: Path,
    schema_name: str,
    total_records: int,
    summary: dict[str, int],
    result: str,
    issues: list[Issue],
) -> None:
    payload = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "schema": schema_name,
        "input": str(input_path),
        "total_records": total_records,
        "error_count": summary["ERROR"],
        "warning_count": summary["WARNING"],
        "info_count": summary["INFO"],
        "result": result,
        "issues": [issue.to_dict() for issue in issues],
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_path)

    try:
        files = iter_input_files(input_path)
        issues, total_records = validate_dataset(
            files=files,
            schema_name=args.schema,
            min_count=args.min_count,
            max_count=args.max_count,
            max_age_days=args.max_age_days,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERROR: unexpected failure: {exc}", file=sys.stderr)
        return 2

    summary = build_summary(issues)
    result = overall_result(summary, args.strict)

    try:
        if args.report:
            write_json_report(Path(args.report), input_path, args.schema, total_records, summary, result, issues)
    except OSError as exc:
        print(f"ERROR: failed to write report: {exc}", file=sys.stderr)
        return 2

    print_report(input_path, args.schema, files, total_records, summary, result, issues, args.quiet)

    if result == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
