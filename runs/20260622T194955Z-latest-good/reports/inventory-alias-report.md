# Inventory Alias Report

Run ID: `20260622T194955Z-latest-good`
Stage: `inventory.alias`
Status: succeeded
Completed: `2026-06-22T19:56:57Z`

## Metrics

| Metric | Value |
| --- | ---: |
| Accepted rows | 20532 |
| CDX pages | 22 |
| Retry events | 0 |
| Failures | 0 |

## Query Results

| Query host | Pages | Accepted rows | Status |
| --- | ---: | ---: | --- |
| `kyledurepos.com` | 11 | 10266 | succeeded |
| `www.kyledurepos.com` | 11 | 10266 | succeeded |

## Retry Details

None

## Failure Details

None

## Outputs

| Artifact | Path |
| --- | --- |
| Raw inventory append | `runs/20260622T194955Z-latest-good/manifests/inventory.raw.jsonl` |
| Alias pass inventory | `runs/20260622T194955Z-latest-good/cdx/alias-inventory.jsonl` |
| CDX page logs | `runs/20260622T194955Z-latest-good/cdx/pages/` |
| Event log | `runs/20260622T194955Z-latest-good/logs/events.jsonl` |
| Retry log | `runs/20260622T194955Z-latest-good/logs/retries.jsonl` |
