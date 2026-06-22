# kyledurepos.com Recovery Progress

**Run ID**: `20260622T194955Z-latest-good`  
**Started**: `2026-06-22T19:49:55Z`  
**Last Updated**: `2026-06-22T21:32:59Z`  

## Stage Status

| Stage | Status | Updated | Notes |
|---|---|---|---|
| init | succeeded | 2026-06-22T19:49:55Z | Run dirs created, DB initialized |
| inventory.primary | succeeded | 2026-06-22T19:58:25Z | 9,541 rows, 10 pages, 1 retry |
| inventory.alias | succeeded | 2026-06-22T19:58:25Z | 20,532 rows, 22 pages |
| selection | succeeded | 2026-06-22T21:19:28Z | 2,947 selected captures after feedback rerun |
| download | succeeded | 2026-06-22T20:23:39Z | 2,941 succeeded, 5 failed, 1 skipped |
| dependencies | succeeded | 2026-06-22T20:32:12Z | 2718 parsed, 575143 refs, 167870 unresolved, 455 high-value missing |
| normalize | succeeded | 2026-06-22T20:35:52Z | 2,941 normalized, 6 failed/skipped |
| inventory.dependencies | succeeded | 2026-06-22T21:14:22Z | 5 rows appended, 77 queries, 2 high-value resolved, 453 unresolved, 0 deferred |
| selection.feedback-1 | succeeded | 2026-06-22T21:19:28Z | consumed 5 dependency rows; 0 net-new selected requiring download |
| model | succeeded | 2026-06-22T21:32:59Z | 2941 modeled; alias 3, asset 225, homepage 1, index 2575, static_page 137; 2538 manual review |
| validate | pending | | |
| privacy | succeeded | 2026-06-22T21:25:53Z | approved-private-only; high 3, medium 5, low 2, info 2; public promotion not approved |
| promote | pending | | |

## Metrics

| Metric | Value |
| --- | ---: |
| CDX records discovered | 30078 |
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
| Broken links | 0 |
| QA failures | 0 |
| High-value missing dependencies | 455 |
| Unresolved first-party dependencies | 167870 |
| Dependency references | 575143 |
| Dependency rows consumed by selection.feedback-1 | 5 |
| Net-new selected requiring download | 0 |
| Content model records | 2941 |
| Content model manual review | 2538 |

## Active Feedback Loops

- _none_

## Decisions/Waivers

_none_
