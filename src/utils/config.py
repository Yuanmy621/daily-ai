from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = BASE_DIR / 'config.yaml'


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.lower() in {'true', 'false'}:
        return value.lower() == 'true'
    if value in {'null', 'None'}:
        return None
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip('"').strip("'")


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or DEFAULT_CONFIG_PATH
    content = config_path.read_text(encoding='utf-8')
    try:
        import yaml  # type: ignore
    except Exception:
        return _simple_yaml_parse(content)
    return yaml.safe_load(content)


def _simple_yaml_parse(content: str) -> dict[str, Any]:
    lines = []
    for raw_line in content.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith('#'):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(' '))
        lines.append((indent, raw_line.strip()))

    index = 0

    def parse_block(expected_indent: int) -> Any:
        nonlocal index
        if index >= len(lines):
            return {}

        if lines[index][1].startswith('- '):
            result_list = []
            while index < len(lines) and lines[index][0] == expected_indent and lines[index][1].startswith('- '):
                item_text = lines[index][1][2:].strip()
                index += 1
                if not item_text:
                    result_list.append(parse_block(expected_indent + 2))
                    continue

                if ':' in item_text:
                    key, _, value = item_text.partition(':')
                    item: dict[str, Any] = {}
                    key = key.strip()
                    value = value.strip()
                    if value:
                        item[key] = _parse_scalar(value)
                    else:
                        item[key] = {}
                    while index < len(lines) and lines[index][0] > expected_indent:
                        child_indent, child_text = lines[index]
                        if child_indent != expected_indent + 2 or child_text.startswith('- '):
                            break
                        child_key, _, child_value = child_text.partition(':')
                        child_key = child_key.strip()
                        child_value = child_value.strip()
                        index += 1
                        if child_value:
                            item[child_key] = _parse_scalar(child_value)
                        else:
                            item[child_key] = parse_block(child_indent + 2)
                    result_list.append(item)
                else:
                    result_list.append(_parse_scalar(item_text))
            return result_list

        result_dict: dict[str, Any] = {}
        while index < len(lines) and lines[index][0] == expected_indent and not lines[index][1].startswith('- '):
            _, text = lines[index]
            key, _, value = text.partition(':')
            key = key.strip()
            value = value.strip()
            index += 1
            if value:
                result_dict[key] = _parse_scalar(value)
            else:
                if index < len(lines) and lines[index][0] == expected_indent + 2 and lines[index][1].startswith('- '):
                    result_dict[key] = parse_block(expected_indent + 2)
                else:
                    result_dict[key] = parse_block(expected_indent + 2)
        return result_dict

    return parse_block(lines[0][0] if lines else 0)


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))
