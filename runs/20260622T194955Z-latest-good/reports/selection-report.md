# Selection Report

Run ID: `20260622T194955Z-latest-good`
Status: succeeded
Generated: `2026-06-22T22:57:11Z`

## Summary

| Metric | Value |
| --- | ---: |
| Raw rows | 30080 |
| Selected captures | 2947 |
| Unique canonical URL identities | 2968 |
| Canonical records | 30080 |
| Aliased records | 21290 |
| Alternate records | 18 |
| Rejected records | 63 |
| Digest-deduped URL identities | 12 |
| Warnings | 1 |

## MIME Distribution

| MIME | Rows |
| --- | ---: |
| `text/html` | 28585 |
| `image/jpeg` | 948 |
| `text/plain` | 359 |
| `image/gif` | 73 |
| `application/x-shockwave-flash` | 42 |
| `missing` | 20 |
| `text/css` | 16 |
| `unk` | 16 |
| `audio/mpeg` | 9 |
| `application/rdf` | 7 |
| `text/xml` | 3 |
| `application/rdf+xml` | 2 |

## MIME Class Distribution

| Class | Rows |
| --- | ---: |
| `html` | 28585 |
| `image` | 1021 |
| `text` | 359 |
| `unknown` | 85 |
| `css` | 16 |
| `audio` | 9 |
| `xml` | 5 |

## Top Route Classes

| Route class | Raw rows | Selected |
| --- | ---: | ---: |
| `query_variant` | 25696 | 2534 |
| `html` | 2532 | 164 |
| `image` | 1021 | 209 |
| `text` | 359 | 12 |
| `html_route` | 239 | 22 |
| `homepage` | 139 | 1 |
| `unknown` | 64 | 0 |
| `css` | 16 | 2 |
| `audio` | 9 | 1 |
| `xml` | 5 | 2 |

## Rejection And Alias Reasons

| Reason | Records |
| --- | ---: |
| `same-normalized-route-or-same-cdx-digest` | 21290 |
| `unexpected-mime-class` | 43 |
| `non-200-status;unexpected-mime-class;missing-required-cdx-field` | 20 |
| `lower-scoring-valid-capture` | 18 |

## Warnings
- 85 raw rows have MIME classes outside the configured expected classes.

## Notes

- URL identity lowercases scheme and host, folds `www.kyledurepos.com` into `kyledurepos.com`, drops fragments, normalizes duplicate path slashes, preserves query strings, and maps HTML index routes consistently.
- CDX digest deduplication selects one fetch representative per digest and records other URL identities as aliases for later route/path handling.
- No content was downloaded during this stage.

## Feedback Rerun Summary

- Stage: `selection.feedback-2`
- Dependency feedback-2 rows consumed: 2
- Prior selected captures preserved by archive URL: 2947
- Prior selected captures no longer selected by archive URL: 0
- Net-new selected captures not present in prior download results: 0
- Download feedback required: no
