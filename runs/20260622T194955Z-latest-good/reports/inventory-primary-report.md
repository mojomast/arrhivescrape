# Inventory Primary Report

Run ID: `20260622T194955Z-latest-good`
Stage: `inventory.primary`
Status: `succeeded`
Started: `2026-06-22T19:54:35.961593Z`
Completed: `2026-06-22T19:56:55.498987Z`

## Query

- Endpoint: `https://web.archive.org/cdx`
- Query kind: `primary_collapsed`
- Query fingerprint: `72289b5a35ecfc62fddb4a87447a8701f41eda0c49610519474ef710f292cffd`
- Stable query URL: `https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&filter=statuscode%3A200&collapse=digest&limit=1000&showResumeKey=true&output=json&fields=urlkey%2Ctimestamp%2Coriginal%2Cmimetype%2Cstatuscode%2Cdigest%2Clength`
- Rate policy: global concurrency 1, minimum 1.1s between CDX request starts

## Metrics

| Metric | Value |
| --- | ---: |
| Pages completed | 10 |
| Rows accepted | 9541 |
| Retries | 1 |

## Outputs

- Raw manifest: `runs/20260622T194955Z-latest-good/manifests/inventory.raw.jsonl`
- Pass JSONL: `runs/20260622T194955Z-latest-good/cdx/primary-collapsed.jsonl`
- Page logs: `runs/20260622T194955Z-latest-good/cdx/pages/`
- Events log: `runs/20260622T194955Z-latest-good/logs/events.jsonl`
- Retries log: `runs/20260622T194955Z-latest-good/logs/retries.jsonl`

## Failures

_none_
