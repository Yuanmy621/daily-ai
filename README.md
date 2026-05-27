# ths_ai_insight

基于多阶段 pipeline 与 Harness Engineering 的 AI 舆情分析日报项目骨架。

## 当前状态

当前仓库已完成：
- 项目架构基线：`AGENT.md`
- 数据鉴定脚本：`check.py`
- 最小工程骨架：目录、配置、pipeline、hooks、skills、tests 占位

## 目录结构

```text
ths_ai_insight/
├── AGENT.md
├── README.md
├── check.py
├── config.yaml
├── data/
├── outputs/
├── prompts/
├── scripts/
├── src/
├── docs/
├── templates/
├── tests/
└── .claude/
```

## 快速开始

```bash
python3 scripts/run_daily.py --date 2026-05-27
python3 check.py data/normalized --schema normalized --min-count 1
```

## 设计原则

- 严禁将全部原始新闻一次性丢给模型直接生成最终日报
- 每个阶段都要输出可检查的中间结果
- 规则性交给代码，主观分析交给模型
- 校验环节独立存在，不由生成环节自验

## 当前骨架包含的阶段

1. collect
2. normalize
3. extract
4. validate_structure
5. cluster
6. insight
7. report
8. visualize
9. validate_final

详细设计见 `AGENT.md` 与 `docs/`。
