from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

TREND_LABELS = {
    'technology': '技术趋势',
    'application': '应用趋势',
    'policy': '政策趋势',
    'capital': '资本趋势',
}



def _bullet_list(items: list[str], empty_text: str = '暂无数据') -> str:
    values = [str(item).strip() for item in items if str(item).strip()]
    if not values:
        return f'- {empty_text}'
    return '\n'.join(f'- {item}' for item in values)



def _render_event_analysis(top_events: list[dict], clusters_by_id: dict[str, dict]) -> str:
    if not top_events:
        return '暂无重点事件。'

    blocks = []
    for index, event in enumerate(top_events[:3], start=1):
        cluster = clusters_by_id.get(event.get('cluster_id', ''), {})
        entities = '、'.join(cluster.get('entities', [])[:5]) or '暂无'
        representative_points = _bullet_list(cluster.get('representative_points', []), empty_text='暂无代表性观点')
        blocks.append(
            '\n'.join(
                [
                    f'### {index}. {event.get("headline", "未命名热点")}',
                    f'- 热度分数：{event.get("heat_score", 0)}',
                    f'- 主题：{cluster.get("topic", "general ai")}',
                    f'- 关联实体：{entities}',
                    '- 代表性观点：',
                    representative_points,
                ]
            )
        )
    return '\n\n'.join(blocks)



def _render_trends(trend_insights: dict) -> str:
    sections = []
    for key, label in TREND_LABELS.items():
        sections.append(f'### {label}\n{_bullet_list(trend_insights.get(key, []))}')
    return '\n\n'.join(sections)



def build_report_context(
    *,
    date: str,
    title: str,
    insight: dict,
    clusters: list[dict],
    visualization_link: str,
) -> dict[str, str]:
    top_events = insight.get('top_events', [])
    clusters_by_id = {cluster.get('cluster_id', ''): cluster for cluster in clusters}
    generated_at = str(insight.get('generated_at', ''))
    sample_size = insight.get('sample_size', 0)

    summary = '\n'.join(
        [
            f'- 日期：{date}',
            f'- 样本量：{sample_size}',
            f'- 热点事件数：{len(top_events)}',
            f'- 生成时间：{generated_at or "未知"}',
        ]
    )
    chart_guide = '\n'.join(
        [
            '- 图表 1：热点事件热度柱状图，用于查看最受关注的事件排序。',
            '- 图表 2：趋势分类分布图，用于查看技术、应用、政策、资本四类趋势的活跃度。',
            '- 图表 3：高频实体 Top N，用于查看当天新闻中最常出现的公司、模型与组织。',
            f'- 交互式可视化：[{visualization_link}]({visualization_link})',
        ]
    )
    methodology = '\n'.join(
        [
            '- 数据来源：配置中的 AI 相关 RSS 源。',
            '- 处理流程：采集 → 标准化 → 结构化抽取 → 聚类 → 洞察生成。',
            '- 生成方式：当前版本以规则抽取和模板渲染为主，便于日常自动化运行。',
        ]
    )

    return {
        'title': title,
        'date': date,
        'summary': summary,
        'hot_topics': _bullet_list([
            f"{item.get('headline', '未命名热点')} (heat={item.get('heat_score', 0)})"
            for item in top_events
        ], empty_text='暂无热点事件'),
        'event_analysis': _render_event_analysis(top_events, clusters_by_id),
        'chart_guide': chart_guide,
        'trend_observation': _render_trends(insight.get('trend_insights', {})),
        'risk_items': _bullet_list(insight.get('risk_alerts', []), empty_text='暂无风险提示'),
        'opportunity_items': _bullet_list(insight.get('opportunity_alerts', []), empty_text='暂无机会提示'),
        'methodology': methodology,
    }



def render_markdown_report(template_text: str, context: dict[str, str]) -> str:
    result = template_text
    for key, value in context.items():
        result = result.replace(f'{{{{ {key} }}}}', value)
    return result.strip() + '\n'
