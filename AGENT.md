# agent.md

## 1. 文档目标

本文档定义 Daily AI Insight Engine 的 agent framework，用于支撑 AI 舆情分析日报系统的 MVP 实现。目标不是简单地“接入多个 AI”，而是把原始新闻到最终日报的处理过程拆成一条可编排、可复用、可校验、可追溯的工程化链路。

本文档服务于以下目标：

- 明确各 agent 的职责边界
- 约束 agent 间的输入输出
- 定义主流程、校验流程与失败回退机制
- 沉淀 prompts、hooks、skills 的组织方式
- 为后续代码实现提供统一设计基线

---

## 2. 设计原则

### 2.1 单一职责
每个 agent 只负责一个明确阶段，不混合承担采集、抽取、分析、成文等多种职责。

### 2.2 分阶段处理
禁止将所有原始新闻一次性输入模型并直接生成最终日报。系统必须经过清洗、抽取、聚合、分析、校验、成文等阶段。

### 2.3 中间结果落盘
每个阶段都必须保存中间产物，便于复查、重跑与验收。

### 2.4 证据驱动分析
所有结论必须能够追溯到结构化字段、事件簇或原始文本证据，避免纯主观生成。

### 2.5 校验独立
负责生成内容的 agent 不负责最终验收，必须由独立 validator 执行格式校验与逻辑校验。

### 2.6 可局部重跑
任意阶段失败后，应优先支持从该阶段或上一阶段重跑，而不是全链路重跑。

---

## 3. 系统目标与边界

### 3.1 目标
系统每天从 10–20 条 AI 相关新闻中提取结构化数据，归纳热点事件，生成一份带可视化内容的 AI 分析日报。

### 3.2 输入边界
输入数据为近期 AI 相关新闻，可来自科技媒体、官方博客、GitHub Releases、社交平台热点或聚合平台。每条数据至少包含：

- title
- content 或 summary
- source
- published_at
- url（如有）
- language（可后置推断）

### 3.3 输出边界
系统至少输出以下内容：

- 结构化新闻数据集
- 聚类后的热点事件结果
- 趋势与洞察分析结果
- 一份完整日报
- 一组可视化结果或图表配置

### 3.4 非目标
当前 MVP 不追求：

- 完整实时爬虫系统
- 大规模多日历史回测
- 全自动无人值守生产化部署
- 通用多领域资讯分析，仅聚焦 AI 主题

---

## 4. 总体架构

采用如下架构：

**Orchestrator + Specialized Agents + Validation Layer + Artifact Store**

职责划分如下：

- Orchestrator：负责任务编排与状态流转
- Specialized Agents：负责具体业务处理阶段
- Validation Layer：负责结构、逻辑与质量校验
- Artifact Store：保存所有中间结果与最终结果

主流程如下：

```text
Source Scout
   ↓
Normalizer
   ↓
Extraction
   ↓
Structure Validator
   ↓
Clustering
   ↓
Insight
   ↓
Logic Validator
   ↓
Report
   ↓
Visualization
   ↓
Final Validator
```

---

## 5. Agent 角色定义

## 5.1 Orchestrator Agent

### 职责
- 接收“生成某日 AI 日报”任务
- 按阶段调度其他 agent
- 控制任务状态与依赖顺序
- 管理输入输出路径
- 触发校验、重试与失败回退

### 输入
- 运行日期
- 数据源配置
- schema 配置
- prompt 模板配置
- pipeline 配置

### 输出
- 每阶段执行状态
- 各阶段 artifact 路径
- 最终日报任务结果

### 不负责
- 不直接产出新闻抽取结果
- 不直接产出分析正文
- 不承担校验裁决逻辑

---

## 5.2 Source Scout Agent

### 职责
- 收集候选新闻
- 过滤出 AI 主题相关内容
- 识别来源类型
- 初步去重
- 生成原始新闻列表

### 输入
- 数据源列表
- 时间范围
- AI 主题过滤条件

### 输出
原始新闻记录，例如：

```json
{
  "id": "raw_001",
  "title": "OpenAI releases new model update",
  "source": "TechCrunch",
  "published_at": "2026-05-27T08:00:00Z",
  "url": "https://example.com/news/1",
  "language": "en",
  "raw_content": "..."
}
```

### 校验重点
- 新闻数量是否达标
- 是否与 AI 主题相关
- 是否存在明显重复

---

## 5.3 Normalizer Agent

### 职责
- 清洗原始文本
- 统一字段命名与时间格式
- 清理广告、噪声、无关段落
- 识别或修正语言标签
- 产出标准化新闻数据

### 输入
- raw news dataset

### 输出
标准化后的新闻记录：

```json
{
  "id": "news_001",
  "title": "OpenAI releases new model update",
  "source": "TechCrunch",
  "published_at": "2026-05-27T08:00:00Z",
  "url": "https://example.com/news/1",
  "language": "en",
  "content": "cleaned content ..."
}
```

### 校验重点
- 必填字段齐全
- 时间格式统一
- 文本长度合理
- 空内容与乱码处理

---

## 5.4 Extraction Agent

### 职责
- 按 schema 对新闻做结构化抽取
- 抽取主题、实体、事件类型、情绪、风险、机会与证据
- 保证输出 JSON 可机器消费

### 输入
- 单条或小批量 normalized news
- extraction schema

### 输出

```json
{
  "id": "news_001",
  "title": "OpenAI releases new model update",
  "source": "TechCrunch",
  "published_at": "2026-05-27T08:00:00Z",
  "language": "en",
  "summary": "OpenAI 发布了新模型更新，重点提升多模态推理能力。",
  "entities": ["OpenAI"],
  "topic": "foundation model",
  "event_type": "product_release",
  "region": "global",
  "importance_score": 8,
  "sentiment": "neutral",
  "risk_signals": ["competition intensifies"],
  "opportunity_signals": ["enterprise adoption"],
  "evidence": [
    "The release includes improved multimodal reasoning.",
    "The company positions the update for enterprise users."
  ]
}
```

### 运行约束
- 单次只处理单条或小批量
- 不允许跨 10–20 条新闻直接生成综合分析
- evidence 必须来自原文，不可凭空补写

### 校验重点
- JSON schema 合法
- evidence 非空
- summary 与原文一致
- importance_score 在可控范围内

---

## 5.5 Clustering Agent

### 职责
- 将结构化新闻按主题或事件聚类
- 合并同一事件的多来源报道
- 识别热点簇与孤立事件
- 生成 cluster-level 表示

### 输入
- structured news dataset

### 输出

```json
{
  "cluster_id": "cluster_01",
  "topic": "foundation model",
  "headline": "多家媒体集中报道 OpenAI 新模型更新",
  "news_ids": ["news_001", "news_006"],
  "entities": ["OpenAI"],
  "heat_score": 9,
  "representative_points": [
    "模型能力更新",
    "企业应用导向加强"
  ]
}
```

### 校验重点
- 相似新闻是否被合并
- 不同事件是否被误聚类
- cluster headline 是否可读

---

## 5.6 Insight Agent

### 职责
- 基于结构化数据与聚类结果提取关键洞察
- 输出热点排行、趋势分析、风险/机会提示
- 保证每个结论可追溯

### 输入
- structured dataset
- clusters

### 输出
建议输出结构：

```json
{
  "top_events": [],
  "trend_insights": {
    "technology": [],
    "application": [],
    "policy": [],
    "capital": []
  },
  "risk_alerts": [],
  "opportunity_alerts": []
}
```

### 分析要求
- Top 事件数量控制在 3–5 条
- 趋势判断至少由多个新闻或 cluster 支撑
- 风险/机会必须具备事实基础

### 校验重点
- 是否存在无证据结论
- 是否只是换种说法重复摘要
- 趋势是否真正跨事件归纳

---

## 5.7 Report Agent

### 职责
- 将洞察内容编排为日报正文
- 统一文风与版式
- 输出 Markdown 或 HTML

### 输入
- insight output
- cluster output
- metadata（日期、样本量、数据源说明）

### 输出建议结构

```markdown
# Daily AI Insight Report

## 今日热点
## 重点事件分析
## 趋势观察
## 风险与机会
## 数据来源与方法
```

### 成文要求
- 先事实，后判断
- 段落短，层次清晰
- 每段尽量对应一个核心观点

---

## 5.8 Visualization Agent

### 职责
- 将结构化与分析结果转为图表数据
- 生成 HTML 图表配置或前端消费数据

### 输入
- structured dataset
- clusters
- insight output

### 输出候选
- 主题分布图
- 热点排行图
- 来源分布图
- 风险/机会矩阵
- 时间线

### 推荐实现
优先输出标准 JSON 配置，例如 ECharts option，以便前端和静态页面复用。

---

## 5.9 Validator Agents

建议拆分为三个 validator，而不是一个全包 validator。

### A. Structure Validator
负责检查：
- JSON 格式
- 必填字段
- schema 一致性
- 字段值类型是否合法

### B. Logic Validator
负责检查：
- 聚类合理性
- 洞察结论是否有依据
- Top 事件排序是否合理
- 趋势是否存在过度泛化

### C. Final Validator
负责检查：
- 日报结构完整
- 可视化与正文是否一致
- 方法说明是否缺失
- 输出是否满足提交要求

---

## 6. 数据模型约定

建议统一使用以下核心 schema。

## 6.1 RawNews

```json
{
  "id": "raw_001",
  "title": "",
  "source": "",
  "published_at": "",
  "url": "",
  "language": "",
  "raw_content": ""
}
```

## 6.2 NormalizedNews

```json
{
  "id": "news_001",
  "title": "",
  "source": "",
  "published_at": "",
  "url": "",
  "language": "",
  "content": ""
}
```

## 6.3 StructuredNews

```json
{
  "id": "news_001",
  "title": "",
  "source": "",
  "published_at": "",
  "language": "",
  "summary": "",
  "entities": [],
  "topic": "",
  "event_type": "",
  "region": "",
  "importance_score": 0,
  "sentiment": "",
  "risk_signals": [],
  "opportunity_signals": [],
  "evidence": []
}
```

## 6.4 EventCluster

```json
{
  "cluster_id": "cluster_01",
  "topic": "",
  "headline": "",
  "news_ids": [],
  "entities": [],
  "heat_score": 0,
  "representative_points": []
}
```

## 6.5 DailyInsight

```json
{
  "date": "2026-05-27",
  "sample_size": 15,
  "top_events": [],
  "trend_insights": {
    "technology": [],
    "application": [],
    "policy": [],
    "capital": []
  },
  "risk_alerts": [],
  "opportunity_alerts": []
}
```

---

## 7. Pipeline 约定

## 7.1 标准执行顺序

### Step 1: Collect
由 Source Scout 生成 `data/raw/*.json`

### Step 2: Normalize
由 Normalizer 生成 `data/normalized/*.json`

### Step 3: Extract
由 Extraction Agent 生成 `data/structured/*.json`

### Step 4: Validate Structure
由 Structure Validator 检查 structured 数据是否合法

### Step 5: Cluster
由 Clustering Agent 生成 `data/clusters/*.json`

### Step 6: Generate Insights
由 Insight Agent 生成 `outputs/insights/*.json`

### Step 7: Validate Logic
由 Logic Validator 检查 insight 是否有事实支撑

### Step 8: Render Report
由 Report Agent 生成 `outputs/reports/*.md` 或 `*.html`

### Step 9: Generate Visualization
由 Visualization Agent 生成 `outputs/visualizations/*.json`

### Step 10: Final Validation
由 Final Validator 检查最终交付完整性

---

## 7.2 失败处理策略

### 结构化失败
表现：JSON 非法、字段缺失、evidence 缺失。

处理：
- 回退到 Extraction
- 缩小批次重试
- 必要时将异常记录列入人工复核清单

### 聚类失败
表现：明显不同事件被混成一类，或重复事件未合并。

处理：
- 回退到 Clustering
- 调整相似度规则或 prompt

### 洞察失败
表现：只有摘要，没有分析；或分析脱离证据。

处理：
- 回退到 Insight
- 强化 evidence 引用约束
- 要求按 cluster 输出 supporting facts

### 成文失败
表现：日报结构不完整、表达空泛、逻辑断裂。

处理：
- 回退到 Report
- 补充模板约束
- 检查上游 insight 输出是否足够结构化

---

## 8. Prompts 组织规范

所有 prompt 必须独立存放，不写死在业务代码中。

建议目录：

```text
prompts/
├── collect/
├── normalize/
├── extract/
├── cluster/
├── insight/
├── report/
└── validate/
```

每个 prompt 文件建议包含：

- 目的说明
- 输入说明
- 输出格式约束
- 示例
- 边界条件

建议命名：

- `extract_news_schema.md`
- `cluster_ai_events.md`
- `generate_daily_insight.md`
- `validate_structured_news.md`
- `render_daily_report.md`

---

## 9. Skills 设计规范

skills 负责沉淀稳定、可复用的能力，不与具体某次运行强绑定。

建议技能如下：

## 9.1 collect-ai-news
### 输入
- date
- source list

### 输出
- raw news json

## 9.2 normalize-news
### 输入
- raw news dataset

### 输出
- normalized news dataset

## 9.3 extract-news-schema
### 输入
- normalized news item(s)
- schema definition

### 输出
- structured news json

## 9.4 cluster-ai-events
### 输入
- structured dataset

### 输出
- event clusters

## 9.5 generate-daily-insight
### 输入
- clusters
- structured dataset

### 输出
- insight json

## 9.6 render-daily-report
### 输入
- insight json
- metadata

### 输出
- markdown/html report

## 9.7 validate-daily-report
### 输入
- report + upstream artifacts

### 输出
- validation issues
- pass/fail result

---

## 10. Hooks 设计规范

hooks 用于阶段边界自动化，不承担主业务决策。

建议目录：

```text
hooks/
├── pre_collect.sh
├── post_collect.sh
├── pre_extract.sh
├── post_extract.sh
├── pre_report.sh
└── post_report.sh
```

## 10.1 Pre-step hooks
用于：
- 校验输入文件存在性
- 检查数据量
- 检查 JSON 基础格式
- 检查配置项是否齐全

## 10.2 Post-step hooks
用于：
- 保存阶段日志
- 产出阶段摘要
- 自动触发 validator
- 更新运行状态文件

## 10.3 Failure hooks
用于：
- 保存错误上下文
- 标记失败数据
- 输出重试建议

约束：
- hooks 不直接调用业务分析逻辑
- hooks 只做边界检查、存档与轻量自动化

---

## 11. Artifact 与目录规范

建议项目目录如下：

```text
daily-ai-insight/
├── data/
│   ├── raw/
│   ├── normalized/
│   ├── structured/
│   └── clusters/
├── outputs/
│   ├── insights/
│   ├── reports/
│   └── visualizations/
├── prompts/
├── skills/
├── hooks/
├── agents/
├── src/
├── REQ.md
├── agent.md
└── README.md
```

目录约束：

- `data/` 保存中间数据
- `outputs/` 保存最终面向阅读者的产物
- `prompts/` 保存 prompt 模板
- `skills/` 保存 skill 说明与调用规范
- `agents/` 保存 agent 角色定义

---

## 12. 运行约定

## 12.1 批处理策略
- 采集阶段可批量
- 抽取阶段建议单条或小批量
- 聚类阶段处理全量 structured dataset
- 分析阶段处理 cluster 级结果，而不是直接处理原始全文集合

## 12.2 模型调用约束
- 大模型主要用于：抽取、聚类辅助、洞察生成、成文与校验
- 简单规则逻辑尽量代码化，例如字段校验、时间格式转换、去重规则
- 优先让模型做“判断与生成”，让程序做“规则与约束”

## 12.3 日志与可追溯
每次运行应保留：
- run id
- 输入文件列表
- 每阶段开始/结束时间
- 每阶段输出路径
- 错误信息与重试记录

---

## 13. 验收标准

agent framework 设计完成后，应至少满足以下标准：

- 能明确解释每个 agent 的职责边界
- 能展示从原始数据到日报的完整处理链路
- 能说明哪些环节由 AI 完成，哪些由程序完成
- 能展示 prompt、hook、skill 的组织方式
- 能支持阶段性校验与失败回退
- 能支撑 REQ.md 要求的 MVP 交付

---

## 14. 推荐后续落地顺序

建议按以下顺序实现：

1. 定义 schema
2. 准备 raw data 样本
3. 实现 normalize pipeline
4. 实现 extract pipeline
5. 实现 structure validator
6. 实现 clustering
7. 实现 insight generation
8. 实现 report renderer
9. 实现 visualization output
10. 接入 hooks、skills 与运行日志

---

## 15. 当前版本结论

本 agent framework 的核心思想是：

- 用 Orchestrator 管流程
- 用 specialized agents 管阶段职责
- 用 validators 管质量
- 用 artifacts 管可追溯
- 用 hooks 与 skills 管工程化沉淀

它适合作为当前 Daily AI Insight Engine 的 MVP 基线，也为后续扩展到自动抓取、多日报对比、长期趋势追踪与多主题分析保留了空间。
