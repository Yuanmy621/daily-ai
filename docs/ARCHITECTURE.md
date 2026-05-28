# Architecture

本文件提供仓库结构的轻量总览，帮助快速定位代码与约束文档。更细的阶段规则见 `docs/PIPELINE.md`，结构校验见 `docs/VALIDATION.md`。

## 总体结构

本项目采用 Orchestrator + Staged Pipeline + Validation Layer 的多阶段架构。

- `scripts/run_daily.py`：统一编排入口，按固定顺序执行 stage
- `src/pipeline/`：各阶段执行模块
- `src/models/`：数据契约定义
- `check.py`：独立结构校验 CLI
- `data/`、`outputs/`：中间与最终产物存储
- `.claude/hooks/`：阶段产物统计与结构校验的自动化 hook
- `.claude/skills/`：后续沉淀稳定可复用 Claude 能力的位置

## `src/` 目录职责

- `src/collector/`：RSS 抓取、来源加载、去重、fallback 样本
- `src/analysis/`：文本清洗、语言识别、规则抽取、evidence 生成
- `src/models/`：`RawNews`、`NormalizedNews`、`StructuredNews`、`EventCluster`、`DailyInsight`
- `src/pipeline/`：collect → validate_final 的 9 个 stage
- `src/report/`：日报 Markdown 上下文组装与模板渲染
- `src/visualize/`：图表 payload 与单文件 HTML dashboard 生成
- `src/utils/`：配置加载、JSON I/O、日志等通用工具

## `.claude/hooks/`

- `check-stage-output.py`：统计 `data/` 与 `outputs/` 中各阶段目录的文件数量，用于快速观察流水线产物是否生成
- `validate-schema.py`：调用 `check.py` 校验 `data/structured/` 下的结构化数据

这两个 hook 都是边界自动化，不承担主业务分析逻辑。
