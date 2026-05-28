# Pipeline

本文件描述当前日报流水线的实现边界、阶段职责、失败回退和局部重跑约束。设计基线可参考 `AGENT.md`，这里以当前代码实现为准。

## 主流程

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

统一入口位于 `scripts/run_daily.py`，每个阶段都必须保持统一接口：

```python
run(date: str, config: dict) -> dict
```

不要破坏这个契约；新增能力应通过新增 stage 或新增独立校验环节接入，而不是把多阶段逻辑塞进单个模块。

## Stage index

`--stage` 参数使用 `scripts/run_daily.py` 中的 index：

1. `0` → `stage_0_collect.py`
2. `1` → `stage_1_normalize.py`
3. `2` → `stage_2_extract.py`
4. `3` → `stage_3_validate_structure.py`
5. `4` → `stage_4_cluster.py`
6. `5` → `stage_5_insight.py`
7. `6` → `stage_6_report.py`
8. `7` → `stage_7_visualize.py`
9. `8` → `stage_8_validate_final.py`

## 全局约束

- 每个 stage 只负责一个明确阶段，不要混合承担采集、抽取、聚类、洞察、成文、可视化与校验。
- 不要绕过分阶段处理直接从原始新闻生成最终日报。
- 每个阶段都必须把结果落盘到 `data/` 或 `outputs/`，不要重构成纯内存链路。
- 阶段失败后优先支持局部重跑，而不是要求整条链路重来。
- 下游阶段应消费上游 artifact，而不是依赖隐藏运行时状态。

## 各阶段职责边界

### `stage_0_collect`
职责：
- 从 `config.yaml` 读取 RSS 数据源
- 抓取候选新闻并去重
- 当实时来源不足时，使用 `src/collector/sample_data.py` 回填样本以满足最小样本量

不负责：
- 不做深度文本清洗
- 不做结构化抽取
- 不输出趋势、风险或机会结论

### `stage_1_normalize`
职责：
- 清洗 HTML/正文
- 统一时间格式到 UTC ISO 格式
- 推断或修正语言标签
- 做 AI 相关性过滤与低信息量过滤
- 在样本不足时补回边界数据，满足 `min_news_count`

不负责：
- 不生成 `topic / event_type / evidence`
- 不输出日报级分析结论

### `stage_2_extract`
职责：
- 将标准化新闻转换为 `StructuredNews`
- 生成 `summary / entities / topic / event_type / region / sentiment / risk_signals / opportunity_signals / evidence`
- 保证输出可被下游聚类与洞察阶段机器消费

关键约束：
- 以单条或小批量处理为主
- 不允许跨全部新闻直接生成综合日报结论
- `evidence` 必须来自原文
- 当前主逻辑位于 `src/analysis/extractor.py`
- `llm_enhance(...)` 当前是 stub，不要假设已有真实 LLM 增强链路

### `stage_3_validate_structure`
职责：
- 调用 `check.py` 校验 structured 数据是否合法
- 在聚类前阻断 schema 不合法或 evidence 不合法的记录

不负责：
- 不修复业务语义
- 不承担聚类或洞察逻辑

### `stage_4_cluster`
职责：
- 基于结构化新闻生成事件簇
- 合并同一事件的多来源报道

注意：
- 当前实现仍偏 scaffold
- 如果热点质量差，优先修这里，而不是在 report 层掩盖上游问题

### `stage_5_insight`
职责：
- 基于 structured + clusters 生成日报级热点、趋势、风险与机会洞察

注意：
- 当前实现仍偏 scaffold
- 如果报表内容空泛，通常问题根源在这里或 `cluster`

### `stage_6_report`
职责：
- 使用 `templates/report_template.md` 渲染 Markdown 日报
- 只消费 insight + clusters，不应自行发明新的事实

### `stage_7_visualize`
职责：
- 生成图表 JSON
- 生成单文件 HTML dashboard
- 当前使用 ECharts CDN，不需要前端构建流程

### `stage_8_validate_final`
职责：
- 检查报表 section 完整性
- 检查 visualization JSON 是否包含 charts
- 检查 HTML 是否包含必要标题和图表容器

## 失败回退原则

- `collect` 失败：先检查 RSS 来源、超时配置、去重与 fallback 样本逻辑。
- `normalize` 失败：先检查文本清洗、时间格式与过滤逻辑，不要在 extract 阶段补洞。
- `extract` 失败：先检查输入内容质量、实体/主题/evidence 抽取逻辑；必要时回退到 normalize。
- `validate_structure` 失败：修 schema 或字段问题，不要绕过 `check.py`。
- `cluster` 失败：修聚类依据，不要在 insight 或 report 层硬编码补救。
- `insight` 失败：补足 cluster 级支撑事实，不要直接写模板化空洞结论。
- `report` 失败：先确认上游 insight 是否足够结构化，再改模板。
- `visualize` 或 `validate_final` 失败：修输出契约，不要删除校验项来“让它通过”。

总原则：优先修上游真实问题，不用跳过阶段、伪造数据或删掉校验来制造成功。

## 局部重跑

- `scripts/run_daily.py --stage <index>` 是标准重跑入口。
- 阶段失败时优先从失败阶段或上一阶段继续执行。
- 保持每个 stage 的输入来自已落盘 artifact，确保局部重跑可重复、可追溯。
