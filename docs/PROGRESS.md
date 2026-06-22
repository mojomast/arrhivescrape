# kyledurepos.com Recovery Progress

**Run ID**: `20260622T194955Z-latest-good`  
**Started**: `2026-06-22T19:49:55Z`  
**Last Updated**: `2026-06-22T22:57:11Z`  

## Stage Status

| Stage | Status | Updated | Notes |
|---|---|---|---|
| init | succeeded | 2026-06-22T19:49:55Z | Run dirs created, DB initialized |
| inventory.primary | succeeded | 2026-06-22T19:58:25Z | 9,541 rows, 10 pages, 1 retry |
| inventory.alias | succeeded | 2026-06-22T19:58:25Z | 20,532 rows, 22 pages |
| selection | succeeded | 2026-06-22T22:57:11Z | 2947 selected captures after feedback-2 rerun |
| download | succeeded | 2026-06-22T20:23:39Z | 2,941 succeeded, 5 failed, 1 skipped |
| dependencies | succeeded | 2026-06-22T20:32:12Z | 2718 parsed, 575143 refs, 167870 unresolved, 455 high-value missing |
| normalize | succeeded | 2026-06-22T20:35:52Z | 2,941 normalized, 6 failed/skipped |
| normalize.feedback-1 | succeeded | 2026-06-22T21:49:51Z | 2712 staged files changed; 486367 refs rewritten/canonicalized; remaining manifest unresolved 87481 |
| inventory.dependencies | succeeded | 2026-06-22T21:14:22Z | 5 rows appended, 77 queries, 2 high-value resolved, 453 unresolved, 0 deferred |
| inventory.dependencies.feedback-2 | succeeded | 2026-06-22T22:19:32Z | 2 rows appended, 196 queries, 1 high-value found, 454 unresolved/static-terminal |
| selection.feedback-1 | succeeded | 2026-06-22T21:19:28Z | consumed 5 dependency rows; 0 net-new selected requiring download |
| selection.feedback-2 | succeeded | 2026-06-22T22:57:11Z | consumed 2 dependency rows; 0 net-new selected requiring download |
| model | succeeded | 2026-06-22T21:32:59Z | 2941 modeled; alias 3, asset 225, homepage 1, index 2575, static_page 137; 2538 manual review |
| validate | blocked | 2026-06-22T21:38:45Z | QA pass 75.0%; blockers 3; public blocked by privacy |
| privacy | succeeded | 2026-06-22T21:25:53Z | approved-private-only; high 3, medium 5, low 2, info 2; public promotion not approved |
| promote | pending | | |

## Metrics

| Metric | Value |
| --- | ---: |
| CDX records discovered | 30080 |
| Inventory primary pages | 10 |
| Inventory alias pages | 22 |
| Inventory primary rows | 9541 |
| Inventory alias rows | 20532 |
| Canonical URLs | 2968 |
| Selected captures | 2947 |
| Downloads attempted | 2947 |
| Downloads succeeded | 2941 |
| Downloads failed | 5 |
| Downloads skipped | 1 |
| Raw objects stored | 2938 |
| Normalized files | 2941 |
| Broken local refs estimate after normalize.feedback-1 | 0 |
| QA failures | 3 |
| High-value missing dependencies | 455 |
| Unresolved first-party dependencies | 167870 |
| Dependency references | 575143 |
| Dependency rows consumed by selection.feedback-1 | 5 |
| Dependency rows consumed by selection.feedback-2 | 2 |
| Net-new selected requiring download | 0 |
| Content model records | 2941 |
| Content model manual review | 2538 |

## Active Feedback Loops

- Validation feedback triage written to `runs/20260622T194955Z-latest-good/reports/validation-feedback-triage.md`.
- Normalization feedback 1 completed: `2712` staged files changed, `486367` references rewritten/canonicalized, `0` estimated broken local refs remain before validation rerun.
- `inventory.dependencies.feedback-2` queried 438 focused high-value static candidates, appended 2 CDX rows, found 1 candidates, and left 454 high-value candidates unresolved or terminal-deferred.
- Human validation waiver is likely needed only for residual low-value dynamic/query references after normalize feedback and high-value dependency recovery; do not waive CSS/JS, homepage/top-level pages, or critical/high-ref images before retry.

- Selection feedback 2 completed: consumed `2` dependency rows, rejected both Flash captures as unsupported MIME, and found `0` net-new selected captures requiring download.

## Decisions/Waivers

- No validation waivers applied. Privacy approval is private-only and does not waive public Funnel blockers.
