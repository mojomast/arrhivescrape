# Serve Validation

Run ID: `20260622T194955Z-latest-good`  
Stage: `promote`  
Generated: `2026-06-22T23:12:53Z`

## Promotion

- Release site: `recovered/kyledurepos.com/releases/20260622T194955Z-latest-good/site/`
- Release manifest: `recovered/kyledurepos.com/releases/20260622T194955Z-latest-good/manifest.jsonl`
- Release reports: `recovered/kyledurepos.com/releases/20260622T194955Z-latest-good/reports/`
- Promoted symlink: `recovered/kyledurepos.com/site -> releases/20260622T194955Z-latest-good/site`
- Rollback target before promotion: none
- Promoted files: `2941`
- Manifest records: `2941`

## Gate Results

- QA gate: `passed-with-waivers`
- Privacy status: `approved-private-only`
- Public Funnel: forbidden and not configured
- Private tailnet exposure: allowed, but not configured automatically due existing Serve config and hostname mismatch

## Caddy

- Status: `available-validated-running`
- Config: `runs/20260622T194955Z-latest-good/ops/Caddyfile`
- Loopback URL: `http://127.0.0.1:18080/`
- PID file: `runs/20260622T194955Z-latest-good/ops/caddy.pid`
- Log file: `runs/20260622T194955Z-latest-good/ops/caddy.log`
- System Caddy config: not modified
- SPA fallback: not configured

## HTTP Validation

| Path | Expected | Actual | Result |
| --- | ---: | ---: | --- |
| `/index.html` | 200 | 200 | passed |
| `/BB/index.html` | 200 | 200 | passed |
| `/BB/login/index.html` | 200 | 200 | passed |
| `/BB/images/smiles/icon_biggrin.gif` | 200 | 200 | passed |
| `/BB/` | 200 | 200 | passed |
| `/journal/archives/000111/` | 200 | 200 | passed |
| `/__validation_missing__.html` | 404 | 404 | passed |
| `/data/kyledurepos.sqlite3` | 404 | 404 | passed |
| `/logs/events.jsonl` | 404 | 404 | passed |
| `/runs/20260622T194955Z-latest-good/config/run-config.json` | 404 | 404 | passed |

## Tailscale Serve

- CLI status: available and authenticated
- Current node DNS: `ussy.tailec998.ts.net`
- Requested hostname: `pwned.ussyco.de`
- Status: `not-configured`
- Reason: current Tailscale Serve config already contains unrelated handlers on `ussy.tailec998.ts.net:443`, and `pwned.ussyco.de` is not the current node's Tailscale DNS/cert domain. Automatic changes were not safe because they could overwrite existing Serve routes or configure the wrong hostname.
- Funnel: not enabled

Private-only manual command if `pwned.ussyco.de` is mapped to this node/service and replacing the current root Serve handler is approved:

```sh
tailscale serve --bg --https=443 http://127.0.0.1:18080
```

Do not run `tailscale funnel` for this release unless privacy is re-approved for public exposure.
