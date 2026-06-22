# QA Summary

Run ID: `20260622T194955Z-latest-good`  
Stage: `validate`  
Generated: `2026-06-22T21:38:45Z`  
Gate status: `blocked`  
QA pass rate: `75.0%`  
Blocking issues: `3`

## Gate Summary

| Check | Status | Failures |
| --- | --- | ---: |
| provenance_completeness | `passed` | 0 |
| sha256_integrity | `passed` | 0 |
| archive_fetch_id_mode | `passed` | 0 |
| mime_audit | `passed` | 0 |
| html_parse_validity | `passed` | 0 |
| internal_link_graph | `failed` | 514456 |
| css_dependency_completeness | `failed` | 2 |
| archive_residue_scan | `passed` | 0 |
| static_serving_smoke | `passed` | 0 |
| browser_dom_smoke | `skipped` | 0 |
| privacy_publication_gate | `blocked_public` | 1 |

## Major Findings

- 514456 staged internal HTML link/resource references are broken
- 2 CSS dependency references are missing
- 167870 unresolved first-party dependency requests remain (455 high-value)

## Static Serving Smoke

- `/index.html` expected 200, got 200 (text/html)
- `/BB/index.html` expected 200, got 200 (text/html)
- `/BB/login/index.html` expected 200, got 200 (text/html)
- `/BB/images/smiles/icon_biggrin.gif` expected 200, got 200 (image/gif)
- `/BB/images/smiles/icon_cool.gif` expected 200, got 200 (image/gif)
- `/BB/` expected 200, got 200 (text/html)
- `/__validation_missing__.html` expected 404, got 404 (HTTP Error 404: File not found)

## Browser/DOM Smoke

- `skipped`: browser automation not available; static HTML parse and HTTP smoke completed

## Privacy Status

- Private-tailnet promotion: approved by privacy report.
- Public Funnel promotion: blocked by privacy report; no validation waiver applied.

## Feedback Loops Required

- dependencies -> inventory.dependencies -> selection -> download -> normalize, focused on unresolved first-party/high-value dependency requests.
- normalize/link rewrite review for broken staged references and missing CSS URL targets.

## Evidence Counts

| Metric | Value |
| --- | ---: |
| Staged public files | 2941 |
| Site manifest records | 2941 |
| Content model records | 2941 |
| Download succeeded | 2941 |
| Download failed | 5 |
| Download skipped | 1 |
| Normalization succeeded | 2941 |
| Dependency graph missing states | 472888 |
| Unresolved first-party dependency requests | 167870 |
| Wayback residue files | 0 |
