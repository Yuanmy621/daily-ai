# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Goal

`ths_ai_insight` 是一个围绕 **AI 资讯采集 → 结构化抽取 → 聚类洞察 → 报表与可视化输出** 构建的分阶段日报流水线。

在这个仓库中工作时，优先目标不是“尽快产出一份结果”，而是维护一条 **可编排、可校验、可追溯、可局部重跑** 的工程化处理链路。

## Big Picture

整体采用：

**Orchestrator + Staged Pipeline + Validation Layer + Artifact Store**

主流程：

```text
collect
  ↓
normalize
  ↓
extract
  ↓
validate_structure
  ↓
cluster
  ↓
insight
  ↓
report
  ↓
visualize
  ↓
validate_final
```

## Hard Constraints

- 单一职责：每个 stage 只负责一个明确阶段，不混合承担采集、抽取、聚类、洞察、成文、可视化与校验。
- 禁止跳阶段：不要把原始新闻一次性送入模型后直接生成最终日报。
- 中间结果落盘：每个阶段都必须把结果写入 `data/` 或 `outputs/`。
- 证据驱动：结论必须可追溯到结构化字段、事件簇或原始文本证据。
- 校验独立：生成阶段不负责裁决自身正确性，validator 必须独立存在。
- 优先局部重跑：阶段失败后优先从失败阶段或上一阶段继续执行。

细则请查阅：
- `docs/PIPELINE.md`
- `docs/SCHEMA.md`
- `docs/VALIDATION.md`
- `docs/USAGE.md`
- `docs/ARCHITECTURE.md`

## Common Commands

```bash
python3 scripts/run_daily.py --date 2026-05-27
python3 scripts/run_daily.py --date 2026-05-27 --stage 3
python3 -m unittest discover tests
```

更多运行、重跑、手工校验命令见 `docs/USAGE.md`。

## Configuration

`config.yaml` 是主要运行控制面，包含：
- pipeline 阈值、batch size、timeout、dedup threshold
- validation 阈值
- artifact 命名规则
- report 标题与语言
- RSS sources 与 AI 关键词字典

当行为差异看起来像规则问题时，先检查 `config.yaml`，再决定是否改代码。

## First Files To Read

1. `README.md` — 产品目标与流水线概览
2. `AGENT.md` — 设计原则与设计基线
3. `docs/PIPELINE.md` — stage 边界、失败回退、局部重跑
4. `docs/SCHEMA.md` — 数据契约与字段变更联动
5. `docs/VALIDATION.md` — validator 角色与验收规则
6. `scripts/run_daily.py` — 实际编排顺序
7. `check.py` — 结构校验规则

## rules
1. 对于修改、新增、现有的代码功能点进行注解说明