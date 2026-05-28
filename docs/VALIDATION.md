# Validation

本文件描述当前项目中的校验原则、validator 职责边界以及最终产物的验收要求。

## 核心原则

### 独立校验
- 生成内容的阶段不负责最终裁决自身是否正确。
- `validate_structure` 与 `validate_final` 必须保持独立 validator 角色。
- 不要把“自检通过”写回生成阶段来替代独立校验。

### 证据驱动
- 所有分析结论都必须能追溯到结构化字段、事件簇或原始文本证据。
- `extract` 阶段生成的 `evidence` 必须来自原文，不可凭空补写。
- `insight`、`report`、`visualize` 只能消费上游结构化结果，不应重新发明未受约束的事实。

### 不允许伪造通过
- 不要通过删除校验项、跳过 validator、补假数据、降低约束来“让流程通过”。
- 如果校验失败，优先修上游真实问题。

## `check.py` 的角色

`check.py` 是当前 `raw / normalized / structured` 的独立校验 CLI，支持：
- 校验单文件或目录
- 支持 JSON / JSONL
- 检查 required fields
- 检查字段类型
- 检查时间格式
- 检查文本长度、URL、重复值
- 检查 structured 的 `importance_score` 与 `evidence` 合法性

常见 issue 类型包括：
- `missing_field`
- `field_type`
- `blank_field`
- `invalid_datetime`
- `importance_range`
- `invalid_evidence`
- `duplicate_id`
- `duplicate_url`
- `duplicate_title`

`ERROR` 会导致失败；`WARNING` 在默认模式下不阻断，但在 strict 模式下可导致失败。

## `validate_structure`

来源：`src/pipeline/stage_3_validate_structure.py`

职责：
- 调用 `check.py` 校验 `data/structured/*.json`
- 在聚类前阻断 schema 不合法的数据

边界：
- 只负责判断 structured 数据是否合法
- 不负责自动修复业务语义
- 不承担聚类或洞察逻辑

如果这个阶段失败，应优先回查：
- `src/analysis/extractor.py`
- `src/pipeline/stage_2_extract.py`
- `docs/SCHEMA.md` 中的字段与类型约束

## `validate_final`

来源：`src/pipeline/stage_8_validate_final.py`

当前最终验收要求：

### Report
Markdown 报表必须包含：
- `## 今日热点`
- `## 重点事件分析`
- `## 趋势观察`
- `## 风险与机会`

### Visualization JSON
- 文件必须存在
- `charts` 字段必须存在且非空

### Visualization HTML
- 文件必须存在
- 必须包含 `<html`
- 必须包含 `config['report']['title']`
- 必须包含 `chart-hot-events`

如果最终校验失败，不要删掉这些检查项；应修复 report、visualize 或其上游输出契约。

## Hooks 中的校验

### `.claude/hooks/validate-schema.py`
- 会扫描 `data/structured/` 下的 JSON/JSONL 文件
- 当前不会校验 insights 文件内容结构
- 使用 `check.py --schema structured --min-count 1` 执行结构校验

### `.claude/hooks/check-stage-output.py`
- 统计 `data/` 与 `outputs/` 各阶段目录中的文件数量
- 用于快速观察流水线产物是否生成
- 它不是 schema validator，只是阶段产物计数器

## 排查原则

- 结构问题先看 `check.py` 的 issue 类型，再回查对应 stage。
- 最终产物问题先看 `report` / `visualize` 是否满足契约，再决定是否上溯到 `insight` 或 `cluster`。
- 不要在 validator 中硬编码业务补救逻辑。
