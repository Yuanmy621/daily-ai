---
name: collect-ai-news
description: Collect raw AI-related news into data/raw with anti-dump constraints.
---

## Purpose
Collect candidate news items for a given date.

## Input
- date
- source list

## Output
- `data/raw/raw_news_<date>.json`

## Constraints
- Do not generate final analysis here.
- Only collect and normalize source metadata.
