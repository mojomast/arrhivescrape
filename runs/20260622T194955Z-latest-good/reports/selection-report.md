# Selection Report

Run ID: `20260622T194955Z-latest-good`
Status: succeeded
Generated: `2026-06-22T20:03:11Z`

## Summary

| Metric | Value |
| --- | ---: |
| Raw rows | 30073 |
| Selected captures | 2947 |
| Unique canonical URL identities | 2968 |
| Canonical records | 30073 |
| Aliased records | 21289 |
| Alternate records | 18 |
| Rejected records | 58 |
| Digest-deduped URL identities | 12 |
| Warnings | 1 |

## MIME Distribution

| MIME | Rows |
| --- | ---: |
| `text/html` | 28583 |
| `image/jpeg` | 948 |
| `text/plain` | 359 |
| `image/gif` | 73 |
| `application/x-shockwave-flash` | 38 |
| `missing` | 20 |
| `text/css` | 16 |
| `unk` | 15 |
| `audio/mpeg` | 9 |
| `application/rdf` | 7 |
| `text/xml` | 3 |
| `application/rdf+xml` | 2 |

## MIME Class Distribution

| Class | Rows |
| --- | ---: |
| `html` | 28583 |
| `image` | 1021 |
| `text` | 359 |
| `unknown` | 80 |
| `css` | 16 |
| `audio` | 9 |
| `xml` | 5 |

## Top Route Classes

| Route class | Raw rows | Selected |
| --- | ---: | ---: |
| `query_variant` | 25695 | 2534 |
| `html` | 2532 | 164 |
| `image` | 1021 | 209 |
| `text` | 359 | 12 |
| `html_route` | 238 | 22 |
| `homepage` | 138 | 1 |
| `unknown` | 60 | 0 |
| `css` | 16 | 2 |
| `audio` | 9 | 1 |
| `xml` | 5 | 2 |

## Rejection And Alias Reasons

| Reason | Records |
| --- | ---: |
| `same-normalized-route-or-same-cdx-digest` | 21289 |
| `unexpected-mime-class` | 38 |
| `non-200-status;unexpected-mime-class;missing-required-cdx-field` | 20 |
| `lower-scoring-valid-capture` | 18 |

## Warnings
- 80 raw rows have MIME classes outside the configured expected classes.

## Notes

- URL identity lowercases scheme and host, folds `www.kyledurepos.com` into `kyledurepos.com`, drops fragments, normalizes duplicate path slashes, preserves query strings, and maps HTML index routes consistently.
- CDX digest deduplication selects one fetch representative per digest and records other URL identities as aliases for later route/path handling.
- No content was downloaded during this stage.
