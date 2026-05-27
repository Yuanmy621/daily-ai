---
name: extract-news-schema
description: Extract structured fields from normalized AI news.
---

## Purpose
Convert normalized news into structured schema records.

## Input
- normalized news dataset

## Output
- `data/structured/structured_news_<date>.json`

## Constraints
- Process small batches only.
- Keep evidence grounded in source text.
