# Usage

本文件收集当前仓库最常用的运行、重跑、校验与测试命令。默认在仓库根目录执行：`/Users/mac148/go_project/Agent/ths_ai_insight`

## 安装依赖

```bash
python3 -m pip install feedparser requests beautifulsoup4 pyyaml jieba
```

`src/utils/config.py` 在 `PyYAML` 缺失时有简易 fallback，但常规开发建议安装 `pyyaml`。

## 运行整条流水线

```bash
python3 scripts/run_daily.py --date 2026-05-27
```

## 从指定阶段继续执行

```bash
python3 scripts/run_daily.py --date 2026-05-27 --stage 3
```

`--stage` index 以 `scripts/run_daily.py` 为准：
- `0` collect
- `1` normalize
- `2` extract
- `3` validate_structure
- `4` cluster
- `5` insight
- `6` report
- `7` visualize
- `8` validate_final

## 手工校验中间产物

```bash
python3 check.py data/raw/raw_news_2026-05-27.json --schema raw --min-count 10
python3 check.py data/normalized/normalized_news_2026-05-27.json --schema normalized --min-count 10
python3 check.py data/structured/structured_news_2026-05-27.json --schema structured --min-count 10
```

## 运行测试

```bash
python3 -m unittest tests/test_pipeline.py
python3 -m unittest tests/test_check.py
python3 -m unittest discover tests
```

## 打开最终可视化页面

```bash
open outputs/visualizations/visualization_2026-05-27.html
```

## 注意事项

- 测试与手工运行都会向带日期的 `data/` / `outputs/` 写文件。
- 如果使用已存在的日期运行，原有同名产物可能会被覆盖。
- 结构校验与最终验收规则请同时参考 `docs/VALIDATION.md`。
