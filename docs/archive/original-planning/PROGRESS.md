# kyledurepos.com Recovery Progress

**Run ID**: `20260622T194955Z-latest-good`  
**Started**: `2026-06-22T19:49:55Z`  
**Last Updated**: `2026-06-25T21:57:40Z`  

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
| validate | passed-with-waivers | 2026-06-22T23:04:25Z | feedback-1 QA pass 100.0%; blockers 0; waivers 2; public blocked by privacy |
| privacy | succeeded | 2026-06-22T21:25:53Z | approved-private-only; high 3, medium 5, low 2, info 2; public promotion not approved |
| promote | succeeded | 2026-06-22T23:12:53Z | promoted release; Caddy loopback validated at `http://127.0.0.1:18080/`; Tailscale Serve not changed; Funnel not enabled |
| tailnet-access | succeeded | 2026-06-23T05:41:59Z | Caddy bound to Tailscale IP `100.72.41.9:18081`; homepage 200 and missing path 404 verified |
| capture-browser | succeeded | 2026-06-23T05:59:31Z | `/captures/` generated; later changed to lazy shard loading: 432 shards, 260 KB index, 30,080 capture rows |
| forum-navigation | succeeded | 2026-06-23T06:59:40Z | repaired phpBB links, added `BB/archive-index/`, wired 2,273 previously unreachable pages |
| forum-ui-assets | succeeded | 2026-06-23T12:15:15Z | phpBB 2.0.6 stock assets replaced 43 placeholders; 7 custom non-stock smiley placeholders remain |
| public-forum-publish | succeeded | 2026-06-24T03:23:19Z | static forum published at `https://ussy.host/archives/websites/pwnedforums/`; no nginx config change; missing path 404 verified |
| forum-media-recovery | partial | 2026-06-24T06:53:52Z | first-party avatar/upload exact recovery found 0; external image pass recovered 8 real archived images and rewrote 1,446 HTML files |

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
| QA failures | 0 |
| High-value missing dependencies | 455 |
| Unresolved first-party dependencies | 167870 |
| Dependency references | 575143 |
| Dependency rows consumed by selection.feedback-1 | 5 |
| Dependency rows consumed by selection.feedback-2 | 2 |
| Net-new selected requiring download | 0 |
| Content model records | 2941 |
| Content model manual review | 2538 |
| Promoted release files | 2941 |
| Promoted manifest records | 2941 |
| Serve validation failures | 0 |
| Capture browser discovered captures | 30080 |
| Capture browser URL groups | 432 |
| Capture browser lazy shards | 432 |
| Forum HTML pages | 2481 |
| Previously unreachable forum pages wired | 2273 |
| Forum archive index pages generated | 13 |
| Forum image references relinked | 248623 |
| phpBB 2.0.6 stock assets restored | 43 |
| Remaining custom phpBB smiley placeholders | 7 |
| Public forum files published | 2558 |
| Public forum HTML files published | 2494 |
| First-party forum media recovery attempted | 80 |
| First-party forum media recovered | 0 |
| External forum media URLs attempted | 50 |
| External forum media recovered | 8 |
| Forum HTML files rewritten for external media | 1446 |

## Active Feedback Loops

- Validation feedback triage written to `runs/20260622T194955Z-latest-good/reports/validation-feedback-triage.md`.
- Normalization feedback 1 completed: `2712` staged files changed, `486367` references rewritten/canonicalized, `0` estimated broken local refs remain before validation rerun.
- `inventory.dependencies.feedback-2` queried 438 focused high-value static candidates, appended 2 CDX rows, found 1 candidates, and left 454 high-value candidates unresolved or terminal-deferred.
- Human validation waiver is likely needed only for residual low-value dynamic/query references after normalize feedback and high-value dependency recovery; do not waive CSS/JS, homepage/top-level pages, or critical/high-ref images before retry.

- Selection feedback 2 completed: consumed `2` dependency rows, rejected both Flash captures as unsupported MIME, and found `0` net-new selected captures requiring download.
- No active pipeline feedback loops remain. Later forum-specific enhancement passes are documented as post-promotion modifications to the promoted release and public copy.

## Decisions/Waivers

- Validation feedback-1 gate status: `passed-with-waivers`; QA pass rate `100.0%`; blocking issues `0`; waivers `2`.
- Waiver for private-tailnet static serving only: residual preserved first-party absolute URLs/high-value dependency gaps were queried or terminally unsupported/unavailable and do not create broken local staged refs or static serving failures.
- Public Funnel promotion remains blocked by privacy review (`approved-private-only`); no public waiver applied.
- Promotion completed to `recovered/kyledurepos.com/releases/20260622T194955Z-latest-good/site/`; `recovered/kyledurepos.com/site` now points to `releases/20260622T194955Z-latest-good/site`.
- Caddy system config was not modified; loopback serving uses `runs/20260622T194955Z-latest-good/ops/Caddyfile` and validated exact paths, directory indexes, missing-path 404s, and non-site artifact 404s.
- Tailscale Serve was not reconfigured because the current node already has unrelated Serve handlers and `pwned.ussyco.de` is not the node's Tailscale DNS/cert domain. Public Funnel remains forbidden and was not enabled.
- Tailnet access was added by binding Caddy to `100.72.41.9:18081` in `runs/20260622T194955Z-latest-good/ops/Caddyfile`; URL: `http://100.72.41.9:18081/`.
- Capture browser is available at `http://100.72.41.9:18081/captures/` and now lazy-loads shard JSON instead of one 15 MB initial payload.
- Forum archive index is available at `http://100.72.41.9:18081/BB/archive-index/` and `https://ussy.host/archives/websites/pwnedforums/archive-index/`.
- Public forum publication is path-scoped to `https://ussy.host/archives/websites/pwnedforums/`; it was implemented as a static copy under `/home/mojo/web/out/archives/websites/pwnedforums` without modifying nginx configuration.
- Public forum HTML is published with `noindex,nofollow` meta tags and rewritten first-party forum links to the obscure public prefix.
- Real phpBB 2.0.6 subSilver assets were restored from the official `phpbb/phpbb` `release-2.0.6` archive; 7 custom non-stock smiley placeholders remain because those filenames were not present in stock phpBB.
- First-party avatar/upload recovery attempted exact Wayback recovery for the top 80 missing assets but recovered 0. External linked-photo recovery attempted the top 50 external image URLs, recovered 8 real archived images, stored them under `BB/recovered-external/`, and republished the public forum.
