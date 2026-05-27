# Architecture

本项目采用 Orchestrator + Specialized Stages + Validation 的多阶段架构。

- `scripts/run_daily.py`：统一编排入口
- `src/pipeline/`：阶段执行模块
- `src/models/`：数据模型定义
- `check.py`：通用结构校验 CLI
- `.claude/hooks/`：阶段输出自动检查
- `.claude/skills/`：后续接入 Claude 能力的技能封装

当前版本先搭建最小可运行骨架，后续逐步填充真实业务逻辑。
