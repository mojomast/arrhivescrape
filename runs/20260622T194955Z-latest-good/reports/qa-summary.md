# QA Summary

Run ID: `20260622T194955Z-latest-good`  
Stage: `validate.feedback-1`  
Generated: `2026-06-22T23:04:25Z`  
Gate status: `passed-with-waivers`  
QA pass rate: `100.0%`  
Blocking issues: `0`  
Waivers: `2`

## Gate Summary

| Check | Status | Failures |
| --- | --- | ---: |
| provenance_completeness | `passed` | 0 |
| sha256_integrity | `passed` | 0 |
| archive_fetch_id_mode | `passed` | 0 |
| mime_audit | `passed` | 0 |
| html_parse_validity | `passed` | 0 |
| internal_link_graph | `passed` | 0 |
| css_dependency_completeness | `passed` | 0 |
| archive_residue_scan | `passed` | 0 |
| static_serving_smoke | `passed` | 0 |
| browser_dom_smoke | `skipped` | 0 |
| privacy_publication_gate | `blocked_public` | 1 |

## Major Findings

- Broken local staged refs after normalize.feedback-1: 0 (previous validation: 514456).
- Missing CSS staged dependencies: 0 (previous validation: 2).
- Preserved external absolute first-party URLs: 943; treated as recovery coverage gaps, not broken local refs.
- External third-party absolute/protocol-relative URLs ignored as local static refs: 6033.
- High-value dependency inventory feedback-2 queried 438 focused candidates, found only Flash `klondike1.swf`, and selection.feedback-2 rejected it as unsupported MIME; 454 high-value dependencies remain unresolved/static-terminal.
- MIME warnings: 1; blocking MIME failures: 0.
- Wayback residue files: 0.

## Waivers
- Residual first-party absolute URLs/high-value dependency gaps are waived for private-tailnet static serving only because normalize.feedback-1 intentionally preserved unresolved first-party URLs as external coverage gaps, focused CDX dependency inventory queried 438 high-value candidates with 0 terminal query errors, the only found Flash candidate was rejected as unsupported MIME, and these gaps do not create broken local staged refs or static serving failures.
- Public Funnel promotion remains blocked by privacy review; private-only privacy approval is not a public waiver.

## Static Serving Smoke
- `/index.html` expected 200, got 200 (text/html)
- `/BB/index.html` expected 200, got 200 (text/html)
- `/BB/login/index.html` expected 200, got 200 (text/html)
- `/BB/images/smiles/icon_biggrin.gif` expected 200, got 200 (image/gif)
- `/BB/images/smiles/icon_cool.gif` expected 200, got 200 (image/gif)
- `/BB/` expected 200, got 200 (text/html)
- `/__validation_missing__.html` expected 404, got 404 (HTTP Error 404: File not found)

## Privacy Status
- Private-tailnet promotion: allowed by privacy report because validation passed with private-only waivers.
- Public Funnel promotion: blocked by privacy report (`approved-private-only`); no public waiver applied.

## Evidence Counts

| Metric | Value |
| --- | ---: |
| Staged public files | 2941 |
| Site manifest records | 2941 |
| HTML files parsed | 2716 |
| HTML/CSS references checked | 606746 |
| Broken local staged refs | 0 |
| Preserved first-party absolute refs | 943 |
| SHA256 failures | 0 |
| Provenance failures | 0 |
