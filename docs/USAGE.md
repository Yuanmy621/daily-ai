# Usage

## 运行骨架 pipeline

```bash
python3 scripts/run_daily.py --date 2026-05-27
```

## 运行数据校验

```bash
python3 check.py data/normalized --schema normalized --min-count 1
python3 check.py data/structured --schema structured --report outputs/reports/validation.json
```

## 运行测试

```bash
python3 -m pytest tests/test_check.py -v
python3 -m pytest tests/test_pipeline.py -v
```
