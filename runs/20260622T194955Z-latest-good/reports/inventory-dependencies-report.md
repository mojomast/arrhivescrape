# Inventory Dependencies Report

Run ID: `20260622T194955Z-latest-good`
Stage: `inventory.dependencies`
Generated: `2026-06-22T21:14:22Z`

## Counts

- Requested rows: 167870
- Deduped first-party URLs: 167869
- Targeted URLs: 455
- CDX queries planned: 77
- CDX requests issued including pages/retries: 77
- Requested URLs with at least one accepted row: 5
- Accepted rows appended: 5
- Deferred URLs: 167414
- Selection must rerun: yes

## High-Value Results

- High-value requested URLs: 455
- High-value resolved: 2
- High-value unresolved: 453
- High-value deferred: 0

## Query Strategy

- Exact CDX lookups were used for query-sensitive HTML directory listings and low-cardinality unique assets.
- Prefix CDX lookups with `collapse=digest` were used for repeated static-asset directories with at least three requested URLs, then filtered back to requested normalized URLs before acceptance.
- The final targeted pass was limited to 455 high-value URLs after an initial broad attempt showed the deduped low-value HTML query space was impractical.
- No content downloads were performed.

## Deferrals

- No targeted high-value URLs were deferred by terminal CDX failure.
- 167075 URLs deferred before query: low-value dynamic HTML session/query variant; one-query-per-reference traffic is impractical and unsafe.
- 244 URLs deferred before query: low-value HTML query variant; deferred in favor of high-value static assets and top-level HTML.
- 95 URLs deferred before query: low-value non-high-value dependency; deferred after high-value prioritization.

## Accepted MIME Distribution

- `application/x-shockwave-flash`: 2
- `text/html`: 2
- `unk`: 1
