# Schema

本文件描述当前代码实现中的数据契约、artifact 包装结构，以及字段变更时需要联动检查的位置。设计原始定义可参考 `AGENT.md`，但当前行为以 `src/models/` 与 `check.py` 为准。

## 核心数据模型

### `RawNews`
来源：`src/models/raw_news.py`

字段：
- `id`
- `title`
- `source`
- `published_at`
- `url`
- `language`
- `raw_content`

### `NormalizedNews`
来源：`src/models/normalized_news.py`

字段：
- `id`
- `title`
- `source`
- `published_at`
- `url`
- `language`
- `content`

### `StructuredNews`
来源：`src/models/structured_news.py`

字段：
- `id`
- `title`
- `source`
- `published_at`
- `language`
- `summary`
- `entities`
- `topic`
- `event_type`
- `region`
- `importance_score`
- `sentiment`
- `risk_signals`
- `opportunity_signals`
- `evidence`

### `EventCluster`
来源：`src/models/event_cluster.py`

字段：
- `cluster_id`
- `topic`
- `headline`
- `news_ids`
- `entities`
- `heat_score`
- `representative_points`

### `DailyInsight`
来源：`src/models/daily_insight.py`

字段：
- `date`
- `sample_size`
- `top_events`
- `trend_insights`
- `risk_alerts`
- `opportunity_alerts`

## Artifact 包装结构

大多数落盘文件不是裸数组，而是包装对象。常见结构：

- `data/raw/*.json`
- `data/normalized/*.json`
- `data/structured/*.json`

通常包含：
- `date`
- `generated_at`
- `articles`

聚类文件通常包含：
- `date`
- `generated_at`
- `clusters`

洞察文件由 `DailyInsight` 展开后写入，并追加 `generated_at`。

修改落盘结构前，先检查所有读取方是否兼容，不要只改写入侧。

## `check.py` 的 schema 名称

`check.py` 当前支持 3 类 schema：

### `raw`
required fields:
- `id`
- `title`
- `source`
- `published_at`
- `raw_content`

文本主字段：`raw_content`

### `normalized`
required fields:
- `id`
- `title`
- `source`
- `published_at`
- `content`

文本主字段：`content`

### `structured`
required fields:
- `id`
- `title`
- `source`
- `published_at`
- `language`
- `summary`
- `entities`
- `topic`
- `event_type`
- `region`
- `importance_score`
- `sentiment`
- `risk_signals`
- `opportunity_signals`
- `evidence`

文本主字段：`summary`

## 字段类型约束概览

`check.py` 中的 `FIELD_TYPES` 约束当前要求：

- `id / title / source / published_at / url / language / raw_content / content / summary / topic / event_type / region / sentiment` 为字符串
- `importance_score` 为 `int` 或 `float`
- `entities / risk_signals / opportunity_signals / evidence` 为列表

另外，`structured` 记录还要求：
- `importance_score` 在 `0..10` 之间
- `evidence` 为非空字符串列表
- `entities / risk_signals / opportunity_signals / evidence` 内部元素都必须是字符串

## 字段变更时必须联动检查

修改 `src/models/` 任意 dataclass 字段时，至少同步检查：

- 对应 stage 的写入逻辑：`src/pipeline/`
- 读取和校验逻辑：`check.py`
- 展示消费方：`src/report/template.py`、`src/visualize/dashboard.py`
- 集成测试：`tests/test_pipeline.py`
- 结构校验测试：`tests/test_check.py`
- 相关文档：`docs/SCHEMA.md`、`docs/VALIDATION.md`

原则：不要只改模型定义而不改校验和下游消费方。
