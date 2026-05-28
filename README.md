# ths_ai_insight

`ths_ai_insight` 是一个围绕 **AI 资讯采集 → 结构化抽取 → 聚类洞察 → 报表与可视化输出** 构建的多阶段日报系统。

它的目标不是“把所有新闻一次性丢给模型生成一篇总结”，而是把整条处理链拆成 **可编排、可校验、可追溯、可局部重跑** 的工程化流水线。当前项目已经具备从 RSS 采集新闻，到生成 Markdown 报表和独立 HTML 可视化页面的一整套基础链路。

---

## 1. 项目目标

这个项目主要解决三类问题：

1. **采集层**：每天从多个 AI 资讯源获取新闻，而不是手工整理
2. **理解层**：把非结构化新闻文本转成可分析的数据对象
3. **交付层**：输出一份可以直接阅读的日报，以及一个可以直接打开的可视化 HTML 页面

当前交付物包括：
- 原始新闻数据集 `data/raw/*.json`
- 标准化新闻数据集 `data/normalized/*.json`
- 结构化新闻数据集 `data/structured/*.json`
- 聚类结果 `data/clusters/*.json`
- 洞察结果 `outputs/insights/*.json`
- 日报 Markdown `outputs/reports/*.md`
- 可视化 JSON `outputs/visualizations/*.json`
- 可视化 HTML `outputs/visualizations/*.html`

---

## 2. 核心设计思想

项目整体采用的是：

**Orchestrator + Staged Pipeline + Validation + Artifact Store**

对应四个核心思想：

### 2.1 Orchestrator 负责流程编排
由 `scripts/run_daily.py` 统一调度每个阶段，保证执行顺序稳定、输入输出路径一致。

### 2.2 每个阶段只做一件事
采集、清洗、抽取、聚类、洞察、成文、可视化、验收分别由独立 stage 完成，避免逻辑缠绕。

### 2.3 中间结果必须落盘
每个阶段都会把结果写到 `data/` 或 `outputs/`，方便：
- 定位问题
- 单独重跑某一阶段
- 对中间结果做人工检查
- 用测试或校验脚本做验收

### 2.4 校验独立于生成
生成阶段负责“产出”，校验阶段负责“验收”。这能避免“自己生成、自己说自己没问题”的假闭环。

---

## 3. 整体框架总览

整体处理链路如下：

```text
RSS Sources / Sample Fallback
        ↓
Stage 0  collect
        ↓
Stage 1  normalize
        ↓
Stage 2  extract
        ↓
Stage 3  validate_structure
        ↓
Stage 4  cluster
        ↓
Stage 5  insight
        ↓
Stage 6  report
        ↓
Stage 7  visualize
        ↓
Stage 8  validate_final
```

你可以把它理解成三层：

### 第一层：数据准备层
- `collect`
- `normalize`
- `extract`

职责是把原始新闻变成结构化对象。

### 第二层：分析归纳层
- `validate_structure`
- `cluster`
- `insight`

职责是把单条新闻转成事件簇与日报洞察。

### 第三层：交付展示层
- `report`
- `visualize`
- `validate_final`

职责是把洞察输出成可阅读、可展示、可验收的最终产物。

---

## 4. 目录结构与职责划分

```text
ths_ai_insight/
├── AGENT.md                    # 整体设计基线与 agent/stage 约束
├── README.md                   # 项目说明与使用手册
├── check.py                    # 数据结构与质量校验 CLI
├── config.yaml                 # 数据源、命名规则、批次参数、校验参数
├── data/                       # 中间数据产物
│   ├── raw/
│   ├── normalized/
│   ├── structured/
│   └── clusters/
├── outputs/                    # 面向阅读者的最终输出
│   ├── insights/
│   ├── reports/
│   └── visualizations/
├── docs/                       # 拆分文档（架构、pipeline、schema 等）
├── prompts/                    # 预留 prompt 组织目录
├── scripts/
│   └── run_daily.py            # 流水线统一入口
├── src/
│   ├── analysis/               # 文本清洗、关键词、规则抽取
│   ├── collector/              # RSS 抓取、来源配置、fallback 样本
│   ├── models/                 # 数据模型 dataclass
│   ├── pipeline/               # 各 stage 的执行模块
│   ├── report/                 # 报表模板渲染
│   ├── utils/                  # 配置、JSON I/O、日志等工具
│   └── visualize/              # HTML 面板与图表数据组装
├── templates/                  # Markdown/HTML 模板
├── tests/                      # 回归测试
└── .claude/                    # hooks / skills / Claude 工程化配置
```

其中最重要的几个位置是：

- `scripts/run_daily.py`：统一入口
- `src/pipeline/`：所有业务 stage
- `src/models/`：数据对象定义
- `check.py`：中间数据与输出数据校验
- `templates/`：报表模板
- `outputs/`：最终产物目录

---

## 5. 关键模块说明

### 5.1 `scripts/run_daily.py`
这是整个项目的主入口，负责：
- 读取 `config.yaml`
- 按顺序执行 stage
- 支持从指定 stage 开始重跑
- 打印每个阶段的结果

当前内置的 stage 顺序定义在 `scripts/run_daily.py` 中：
- `collect`
- `normalize`
- `extract`
- `validate_structure`
- `cluster`
- `insight`
- `report`
- `visualize`
- `validate_final`

### 5.2 `src/models/`
定义了 5 个核心数据模型：
- `RawNews`
- `NormalizedNews`
- `StructuredNews`
- `EventCluster`
- `DailyInsight`

这些 dataclass 决定了中间结果如何落盘，也决定了下游 stage 能读取哪些字段。

### 5.3 `src/collector/`
负责采集层：
- 从 `config.yaml` 中读取 RSS 数据源
- 通过 `rss_fetcher.py` 抓取内容
- 做去重和内容清洗
- 当外部 RSS 不可用时，用 `sample_data.py` 回填样本，保证 pipeline 最低可运行性

### 5.4 `src/analysis/`
负责结构化前后的文本处理：
- HTML 清理
- 语言识别
- 关键词抽取
- topic / event_type / entity / sentiment / evidence 规则抽取

这是当前“规则逻辑主要落在代码里”的核心区域。

### 5.5 `src/pipeline/`
每个阶段都通过 `run(date, config)` 暴露统一接口，便于编排器调用。

### 5.6 `src/report/` 与 `src/visualize/`
这是当前新增的展示层：

- `src/report/template.py`
  - 负责把 insight + cluster 数据组装成 Markdown 报表上下文
  - 用模板填充出完整日报

- `src/visualize/dashboard.py`
  - 负责把 insight + cluster + structured 数据组装成图表 payload
  - 生成单文件 HTML 页面
  - 当前使用 ECharts CDN 直接渲染，不依赖前端构建系统

### 5.7 `check.py`
这是项目的通用数据鉴定脚本，可以直接验证：
- `raw`
- `normalized`
- `structured`

它支持：
- 包装对象读取（包含 `articles`）
- JSON / JSONL 文件
- 字段完整性检查
- 类型检查
- 时间格式检查
- 文本长度检查
- URL 检查
- 重复检查
- structured evidence 合法性检查

---

## 6. 数据流详细说明

项目里最核心的是数据在不同阶段的演变过程。

### 6.1 RawNews
来源于 `collect` 阶段，表示“刚抓下来、还没标准化”的原始新闻。

典型字段：
- `id`
- `title`
- `source`
- `published_at`
- `url`
- `language`
- `raw_content`

### 6.2 NormalizedNews
来源于 `normalize` 阶段，表示“已经清洗和标准化”的新闻。

典型变化：
- `raw_content` 被清洗为 `content`
- 时间被格式化成 ISO 8601
- language 被修正
- 非 AI 相关或低信息量内容可能被过滤

### 6.3 StructuredNews
来源于 `extract` 阶段，表示“已经可分析”的结构化新闻。

新增字段包括：
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

### 6.4 EventCluster
来源于 `cluster` 阶段，表示“多条新闻归并后的热点事件簇”。

典型字段：
- `cluster_id`
- `topic`
- `headline`
- `news_ids`
- `entities`
- `heat_score`
- `representative_points`

### 6.5 DailyInsight
来源于 `insight` 阶段，表示“日报级别的聚合洞察”。

典型字段：
- `date`
- `sample_size`
- `top_events`
- `trend_insights`
- `risk_alerts`
- `opportunity_alerts`

### 6.6 报表与可视化输出
最终由展示层输出为：
- `daily_report_<date>.md`
- `visualization_<date>.json`
- `visualization_<date>.html`

这一步把数据模型变成最终可阅读材料。

---

## 7. 各阶段职责详解

### Stage 0 — collect
文件：`src/pipeline/stage_0_collect.py`

职责：
- 聚合 RSS 数据源
- 抓取新闻
- 去重
- 数量不足时回填 sample 数据

输出：`data/raw/raw_news_<date>.json`

### Stage 1 — normalize
文件：`src/pipeline/stage_1_normalize.py`

职责：
- 清洗文本
- 统一时间格式
- 修正语言
- AI 相关性过滤
- 低信息量内容过滤与兜底补齐

输出：`data/normalized/normalized_news_<date>.json`

### Stage 2 — extract
文件：`src/pipeline/stage_2_extract.py`

职责：
- 对标准化新闻进行规则抽取
- 生成 summary / entities / topic / event_type / evidence 等字段

输出：`data/structured/structured_news_<date>.json`

### Stage 3 — validate_structure
文件：`src/pipeline/stage_3_validate_structure.py`

职责：
- 调用 `check.py`
- 校验 structured 数据是否满足 schema 要求

### Stage 4 — cluster
文件：`src/pipeline/stage_4_cluster.py`

职责：
- 根据结构化新闻生成热点事件簇

当前状态：已可运行，但仍偏 scaffold。

### Stage 5 — insight
文件：`src/pipeline/stage_5_insight.py`

职责：
- 从 cluster 中生成热点、趋势、风险与机会洞察

当前状态：已可运行，但仍偏 scaffold。

### Stage 6 — report
文件：`src/pipeline/stage_6_report.py`

职责：
- 把 `DailyInsight + EventCluster` 渲染为 Markdown 图文报表

输出：`outputs/reports/daily_report_<date>.md`

### Stage 7 — visualize
文件：`src/pipeline/stage_7_visualize.py`

职责：
- 生成图表 JSON
- 生成可直接打开的 HTML 页面

输出：
- `outputs/visualizations/visualization_<date>.json`
- `outputs/visualizations/visualization_<date>.html`

### Stage 8 — validate_final
文件：`src/pipeline/stage_8_validate_final.py`

职责：
- 检查 Markdown 报表 section 是否齐全
- 检查 visualization JSON 是否有 charts
- 检查 HTML 页面是否包含标题和图表容器

---

## 8. 当前项目状态评估

从整体框架看，当前项目已经不是纯骨架，而是一个 **可运行的日报系统基础版**：

### 已经具备的能力
- RSS 抓取 + fallback 样本机制
- 规范化数据清洗
- 规则抽取结构化字段
- 中间结果落盘
- 原生 `check.py` 校验
- Markdown 日报输出
- HTML 可视化页面输出
- 测试回归链路

### 仍然偏占位的部分
- `cluster` 阶段还比较简单
- `insight` 阶段还没有做足够真实的日报级归纳
- 报表和图表的“展示壳”已经完整，但上游洞察内容仍可继续提升

所以当前最准确的判断是：

> 展示层已经具备交付形态，数据准备层已经具备真实能力，分析归纳层还需要继续从 scaffold 升级到真实版本。

---

## 9. 如何运行项目

### 9.1 安装依赖

建议先安装：

```bash
python3 -m pip install feedparser requests beautifulsoup4 pyyaml jieba
```

说明：
- `feedparser / requests / beautifulsoup4` 用于 RSS 抓取
- `jieba` 用于中文关键词与分词增强
- 即使部分 RSS 源失败，项目也会通过 fallback 样本保持最小可运行

### 9.2 运行整条流水线

```bash
cd /Users/mac148/go_project/Agent/ths_ai_insight
python3 scripts/run_daily.py --date 2026-05-27
```

如果只想从某个阶段开始重跑：

```bash
python3 scripts/run_daily.py --date 2026-05-27 --stage 3
```

其中 `--stage` 表示从第几个 stage index 开始继续执行。

### 9.3 查看输出

运行完成后，重点看：

```text
data/raw/raw_news_2026-05-27.json
data/normalized/normalized_news_2026-05-27.json
data/structured/structured_news_2026-05-27.json
data/clusters/clusters_2026-05-27.json
outputs/insights/daily_insight_2026-05-27.json
outputs/reports/daily_report_2026-05-27.md
outputs/visualizations/visualization_2026-05-27.json
outputs/visualizations/visualization_2026-05-27.html
```

直接打开 HTML：

```bash
open outputs/visualizations/visualization_2026-05-27.html
```

---

## 10. 如何做数据校验

### 校验 raw

```bash
python3 check.py data/raw/raw_news_2026-05-27.json --schema raw --min-count 10
```

### 校验 normalized

```bash
python3 check.py data/normalized/normalized_news_2026-05-27.json --schema normalized --min-count 10
```

### 校验 structured

```bash
python3 check.py data/structured/structured_news_2026-05-27.json --schema structured --min-count 10
```

你会看到：
- `PASS` / `FAIL`
- `ERROR / WARNING / INFO`
- 每个问题对应的 `record_id`

说明：
- `WARNING` 常见于内容过短或来源摘要过短，不一定代表流程失败
- `ERROR` 才表示需要优先处理的问题

---

## 11. 如何运行测试

```bash
python3 -m unittest tests/test_pipeline.py
```

当前测试会检查：
- 流水线能否完整跑通
- raw / normalized / structured 文件是否存在
- insight / report / visualization JSON / visualization HTML 是否存在
- structured 数据是否不再是纯占位值
- Markdown 报表是否包含关键 section
- HTML 是否包含标题、ECharts 和图表容器

---

## 12. 配置文件说明

`config.yaml` 是项目行为的统一入口，主要配置：

### pipeline
控制：
- 最少 / 最多新闻数
- 各阶段 batch size
- RSS timeout
- 去重阈值

### validation
控制：
- 最小内容长度
- 最大内容长度
- 是否严格模式

### naming
控制各类输出文件命名模板。

### sources
定义 RSS 数据源，当前按：
- `chinese`
- `english`

分组组织。

### keywords
定义 AI 主题识别关键词，按：
- `zh`
- `en`

分组组织。

---

## 13. 与 AGENT.md / docs 的关系

如果你想继续深入理解设计，有三份文档建议一起看：

- `AGENT.md`
  - 偏“设计基线”
  - 讲的是为什么要这样拆、每个角色负责什么

- `docs/ARCHITECTURE.md`
  - 偏“结构概览”
  - 讲的是模块分工

- `docs/PIPELINE.md`
  - 偏“执行顺序”
  - 讲的是 stage 链路

而这份 `README.md` 的角色是：

> 让第一次接触这个项目的人，既能理解它的整体框架，也能直接上手运行。

---

## 14. 下一步建议

如果继续往下完善，建议优先做这两件事：

1. **升级 `stage_4_cluster.py`**
   - 让 cluster 真正基于 topic / entities / headline 相似性聚类

2. **升级 `stage_5_insight.py`**
   - 让日报热点、趋势、风险、机会来自真实 cluster 与 structured 数据

完成这两层后：
- 当前已经做好的 Markdown 报表
- 当前已经做好的 HTML 可视化

就会从“展示框架完善”升级为“内容也真实可靠”。
