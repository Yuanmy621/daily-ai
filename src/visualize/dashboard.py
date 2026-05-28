from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]



def _top_entities(clusters: list[dict], structured_articles: list[dict], limit: int = 8) -> list[dict]:
    counter: Counter[str] = Counter()
    for cluster in clusters:
        counter.update(entity for entity in cluster.get('entities', []) if entity)
    for article in structured_articles:
        counter.update(entity for entity in article.get('entities', []) if entity)
    return [
        {'label': label, 'value': value}
        for label, value in counter.most_common(limit)
    ]



def build_visualization_payload(date: str, insight: dict, clusters: list[dict], structured_articles: list[dict]) -> dict:
    top_events = insight.get('top_events', [])
    trend_insights = insight.get('trend_insights', {})
    charts = [
        {
            'type': 'bar',
            'title': '热点事件热度',
            'data': [
                {'label': item.get('headline', '未命名热点'), 'value': item.get('heat_score', 0)}
                for item in top_events
            ],
        },
        {
            'type': 'bar',
            'title': '趋势分类分布',
            'data': [
                {'label': '技术', 'value': len(trend_insights.get('technology', []))},
                {'label': '应用', 'value': len(trend_insights.get('application', []))},
                {'label': '政策', 'value': len(trend_insights.get('policy', []))},
                {'label': '资本', 'value': len(trend_insights.get('capital', []))},
            ],
        },
        {
            'type': 'bar',
            'title': '高频实体 Top N',
            'data': _top_entities(clusters, structured_articles),
        },
    ]
    return {
        'date': date,
        'summary': {
            'sample_size': insight.get('sample_size', 0),
            'hot_event_count': len(top_events),
            'cluster_count': len(clusters),
        },
        'highlights': [item.get('headline', '未命名热点') for item in top_events[:5]],
        'risk_alerts': insight.get('risk_alerts', []),
        'opportunity_alerts': insight.get('opportunity_alerts', []),
        'charts': charts,
    }



def render_dashboard_html(title: str, payload: dict) -> str:
    payload_json = json.dumps(payload, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{title}</title>
  <script src=\"https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js\"></script>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: #f5f7fb; color: #1f2937; }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    .hero {{ background: linear-gradient(135deg, #2563eb, #0f172a); color: white; padding: 24px; border-radius: 16px; }}
    .cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 20px 0; }}
    .card, .panel {{ background: white; border-radius: 16px; padding: 20px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08); }}
    .charts {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
    .chart {{ height: 360px; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }}
    h1, h2, h3 {{ margin-top: 0; }}
    ul {{ margin: 0; padding-left: 20px; }}
    .muted {{ color: #cbd5e1; }}
    @media (max-width: 900px) {{ .cards, .two-col {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class=\"container\">
    <section class=\"hero\">
      <h1>{title}</h1>
      <p>日期：<span id=\"report-date\"></span></p>
      <p class=\"muted\">基于每日 AI 资讯采集、结构化抽取、聚类与洞察结果自动生成。</p>
    </section>
    <section class=\"cards\">
      <div class=\"card\"><h3>样本量</h3><p id=\"sample-size\"></p></div>
      <div class=\"card\"><h3>热点事件数</h3><p id=\"hot-event-count\"></p></div>
      <div class=\"card\"><h3>聚类数</h3><p id=\"cluster-count\"></p></div>
    </section>
    <section class=\"charts\">
      <div class=\"panel\"><h2>热点事件热度</h2><div id=\"chart-hot-events\" class=\"chart\"></div></div>
      <div class=\"panel\"><h2>趋势分类分布</h2><div id=\"chart-trends\" class=\"chart\"></div></div>
      <div class=\"panel\"><h2>高频实体 Top N</h2><div id=\"chart-entities\" class=\"chart\"></div></div>
    </section>
    <section class=\"two-col\">
      <div class=\"panel\">
        <h2>热点摘要</h2>
        <ul id=\"highlight-list\"></ul>
      </div>
      <div class=\"panel\">
        <h2>风险与机会</h2>
        <h3>风险</h3>
        <ul id=\"risk-list\"></ul>
        <h3>机会</h3>
        <ul id=\"opportunity-list\"></ul>
      </div>
    </section>
  </div>
  <script>
    const payload = {payload_json};
    document.getElementById('report-date').textContent = payload.date;
    document.getElementById('sample-size').textContent = payload.summary.sample_size;
    document.getElementById('hot-event-count').textContent = payload.summary.hot_event_count;
    document.getElementById('cluster-count').textContent = payload.summary.cluster_count;

    const renderList = (elementId, items, emptyText) => {{
      const target = document.getElementById(elementId);
      const values = items && items.length ? items : [emptyText];
      target.innerHTML = values.map(item => `<li>${{item}}</li>`).join('');
    }};

    renderList('highlight-list', payload.highlights, '暂无热点摘要');
    renderList('risk-list', payload.risk_alerts, '暂无风险提示');
    renderList('opportunity-list', payload.opportunity_alerts, '暂无机会提示');

    const renderBarChart = (elementId, chart) => {{
      const instance = echarts.init(document.getElementById(elementId));
      instance.setOption({{
        tooltip: {{ trigger: 'axis' }},
        grid: {{ left: 60, right: 24, top: 30, bottom: 80 }},
        xAxis: {{
          type: 'category',
          data: chart.data.map(item => item.label),
          axisLabel: {{ interval: 0, rotate: 25 }}
        }},
        yAxis: {{ type: 'value' }},
        series: [{{
          type: 'bar',
          data: chart.data.map(item => item.value),
          itemStyle: {{ color: '#2563eb' }},
          barMaxWidth: 48,
        }}],
      }});
    }};

    renderBarChart('chart-hot-events', payload.charts[0]);
    renderBarChart('chart-trends', payload.charts[1]);
    renderBarChart('chart-entities', payload.charts[2]);
  </script>
</body>
</html>
"""
