# Validation Feedback Triage

Run ID: `20260622T194955Z-latest-good`  
Generated: `2026-06-22T21:43:40Z`  
Role: Validation Feedback Triage Agent

## Decision Summary

Gate status remains `blocked`. The three validation blockers are not all equivalent:

| Blocker | Count | Triage | Next action |
| --- | ---: | --- | --- |
| Internal link graph | 514456 broken staged refs | Mixed: mostly dynamic/query references plus normalization rewrite gaps | Run `normalize.feedback`; waive residual low-value dynamic query refs after owner approval |
| CSS dependency completeness | 2 missing CSS URL targets | True missing assets | Run targeted `inventory.dependencies`/download or waive/substitute |
| Unresolved first-party dependencies | 167870 requests, 455 high-value in request manifest; 453 high-value unresolved after dependency inventory feedback | Mixed: high-value assets/pages plus low-value dynamic/query space | Re-run focused `inventory.dependencies` for recoverable high-value assets; waive unrecoverable dynamic/query tail |

## Category 1: Missing High-Value Assets/Pages Needing Inventory/Download

Counts from `missing-dependency-requests.jsonl`:

| Class | Total missing requests | High-value requests |
| --- | ---: | ---: |
| html | 167407 | 14 |
| image | 427 | 427 |
| audio | 4 | 4 |
| css | 3 | 3 |
| javascript | 3 | 3 |
| unknown | 26 | 4 |

Post-feedback status from `inventory-dependencies-report.md`: `455` high-value targeted, `2` resolved, `453` still unresolved, `5` accepted rows appended, and `167414` requests deferred.

Recoverable priorities:

- First-party audio: `audio/atmosphere-04-fuck_you_lucy-wcr.mp3`, `audio/badabing.mp3`, `audio/mm3theme.mp3`, `~rtdrb/satnight.mp3`.
- First-party CSS/JS: `hellslayer.kyledurepos.com/podcast/wp-content/plugins/coolplayer/coolplayer.css`, `coolplayer.js`, `phprpc_client.js`, `hellslayer.kyledurepos.com/podcast/wp-content/themes/orange-subway-10/style.css`, `kyledurepos.com/dgclan/themes/Kaput/style/style.css`.
- High-ref phpBB chrome/smilies/template images: e.g. `BB/images/smiles/icon_eek.gif` (472 refs), `BB/images/smiles/lol.gif` (387 refs), `BB/templates/subSilver/images/icon_mini_faq.gif` (2484 refs).
- CSS blocker images from `mt-static/styles.css`: `mt-static/images/bar-back.gif` and `mt-static/images/logo-small.gif`.

Go/no-go for `inventory.dependencies`: go for a focused high-value static asset pass. Do not broaden to all `167870` request rows; prior inventory already found that one-query-per-reference dynamic HTML space is impractical.

## Category 2: Normalization/Rewrite Fixes Not Requiring New CDX Rows

Observed patterns:

- phpBB session IDs dominate: `167075` dependency request URLs contain `sid`; `232658` missing dependency-graph rows contain `sid`.
- Query URLs dominate: `167333` dependency request URLs and `233215` missing dependency-graph rows contain a query string.
- `111898` missing request URLs have a path-only staged target after dropping the query; `111656` of those are `sid` variants.
- `142434` missing dependency-graph rows have a path-only staged target after dropping the query.
- Broken staged samples show relative links left unresolved inside materialized query pages, e.g. `BB/login/index.html` has `./index.php?...` resolving as `BB/login/index.php` instead of canonical `BB/index.php` or staged `BB/`.
- Normalization records show `links_rewritten: 0` for affected phpBB HTML while unresolved internal targets include path-only assets and pages that often already exist in `site.manifest.jsonl`.

Recommended `normalize.feedback` changes:

- For phpBB URLs, strip transient `sid` when resolving/writing links, preserving stable content parameters such as `t`, `p`, `f`, `u`, `mode`, and anchors only when a matching staged query capture exists.
- If no matching query capture exists but the path-only target is staged, rewrite to the path-only staged page instead of leaving the original query URL.
- Resolve relative phpBB chrome/template assets from their original URL context, not from the nested output path created for query pages such as `BB/login/index.html`.
- Re-run validation after normalization feedback before considering waivers; this should materially reduce the `internal_link_graph` blocker without new CDX rows.

Go/no-go for `normalize.feedback`: go. This blocker is substantially resolvable by prior-stage normalization logic and should not be waived before a rewrite pass.

## Category 3: Low-Value/Dynamic/Query References For Waiver Consideration

Counts and examples:

- `167075` requests were deferred before query as low-value dynamic HTML session/query variants.
- `244` additional low-value HTML query variants were deferred in favor of high-value static assets and top-level HTML.
- Top query keys include `sid` (167075), `mode` (80778), `p` (60912), `u` (40530), `f` (26930), `t` (13852), `start` (6343), `view` (4912), `postdays`/`postorder` (3839 each), `folder` (2486), and `highlight` (2462).
- Examples include phpBB profile/memberlist/private-message/action links, guestbook/comment pagination, WordPress feeds/category/month/archive query pages, and Apache directory sort variants such as `?D=A`, `?M=D`, `?N=A`, `?S=D`.

Waiver stance:

- Candidate for waiver only after static assets and rewriteable path-only references have been addressed.
- Do not waive homepage/top-level pages, CSS/JS, critical images, or high-ref shared chrome assets.
- Human waiver is needed for the residual dynamic/query tail because the validation gate is currently strict and the evidence shows intentional deferral rather than successful recovery.

## Blocker Resolvability

| Validation blocker | Resolvable by prior stages? | Human waiver needed? |
| --- | --- | --- |
| `internal_link_graph` | Partially. Normalize feedback can rewrite many `sid`/path-only and relative-context failures. Residual low-value dynamic query refs likely remain. | Yes, but only for residual dynamic/query refs after normalize feedback and high-value asset passes. |
| `css_dependency_completeness` | Yes if CDX rows can be found/downloaded for two `mt-static` images; otherwise no. | Yes if exact CDX retry still finds no rows or owner accepts visual degradation/substitution. |
| `privacy_publication_gate` | Not a recovery-stage issue. Privacy report blocks public promotion. | Yes for public promotion; private-tailnet promotion is approved by privacy report. |

## Recommended Feedback Stages

1. Run `normalize.feedback` first for phpBB `sid` stripping, path-only fallback rewrites, and relative asset context fixes.
2. Run focused `inventory.dependencies` for remaining high-value static assets: phpBB chrome/smilies/templates, `mt-static` CSS images, audio, CSS, JS, and high-value subdomain assets.
3. Re-run `selection`, `download`, `normalize`, and `validate` on accepted dependency rows.
4. Prepare a human validation waiver only for residual low-value dynamic/query references that remain after the above passes.
