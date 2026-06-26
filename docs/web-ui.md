# Local Web UI

The web UI is an optional local operator console for Archive Recovery Toolkit targets and runs. It uses the same config renderer, run initializer, and pipeline functions as the CLI, and it reads/writes the normal ignored config and run directories. It does not publish recovered sites.

## Install And Start

Install the optional web dependencies from the repo root:

```bash
python -m pip install -e '.[web]'
```

You can create a target config and initialize a run from the browser, or use the CLI first:

```bash
archive-recovery new --domain example.com --non-interactive
archive-recovery init --config configs/example.com.toml --run-id my-first-run
```

Start the local dashboard:

```bash
archive-recovery web --runs-root runs --config configs/example.com.toml
```

Open `http://127.0.0.1:18080/`. The default bind is loopback-only. To bind outside loopback, pass a non-local `--host`, `--allow-nonlocal`, and an auth token through `--auth-token` or `--auth-token-file`. The app rejects unauthenticated non-loopback startup unless `--unsafe-no-auth` is explicitly provided for isolated throwaway testing.

For a browser-only setup, open `/targets/new`, create a conservative target config under `configs/`, then open `/runs` and initialize a run from that config. The browser form uses the same TOML renderer and validation as `archive-recovery new`; it accepts a simple `.toml` filename only and writes under `configs/`.

For private tailnet access to the operator web UI, prefer a local web process plus an explicit Tailscale-only exposure. Keep it off the public internet unless the target has passed validation and privacy review. One direct web UI bind option is:

```bash
TAILSCALE_IP=$(tailscale ip -4)
archive-recovery web --runs-root runs --config configs/example.com.toml --host "$TAILSCALE_IP" --port 18080 --allow-nonlocal --auth-token "$ARCHIVE_RECOVERY_WEB_TOKEN"
```

Then open `http://<tailscale-ip>:18080/` from another device in the same tailnet. If using `tailscale serve`, keep the target local-only and verify the route before sharing it:

```bash
archive-recovery web --runs-root runs --config configs/example.com.toml --port 18080
tailscale serve --bg --yes http://127.0.0.1:18080
tailscale serve status
```

When a proxy, MagicDNS hostname, or Tailscale Serve forwards requests to a loopback web process, include every browser-facing host with `--allowed-host`, such as the Tailscale IP, short host, and MagicDNS name. Unsafe requests still require CSRF, but trusted Origin checks accept either the direct request host, an explicitly allowed `X-Forwarded-Host`/`X-Forwarded-Proto` origin, or an Origin whose host is in the allowed-host list. This covers common Tailscale IP, port, MagicDNS, and HTTPS variants while unlisted Origin hosts are still rejected.

## Local Operation Model

- The app is served by `uvicorn` and the optional Starlette/Jinja2 web package.
- `--runs-root` selects the run directory root to browse; default is `runs`.
- `--config` provides a default TOML config for starting stages when the run does not already have a frozen config path.
- Browser-created configs are written under `configs/`; existing configs are not overwritten unless `force=true` is submitted.
- Browser-created runs must use a config whose `paths.runs_root` matches the web process `--runs-root`; initialization freezes `runs/<run_id>/config/run-config.json` and registers the run in the configured SQLite state database.
- Run config, manifests, reports, logs, and status stay under the existing ignored run directory layout.
- Stage output is produced by the same package pipeline modules used by `archive-recovery inventory`, `select`, `download`, `dependencies`, `dependency-recovery`, `normalize`, `validate`, and `captures-browser`.
- HTML forms and unsafe API methods require CSRF tokens. Browser-originated unsafe requests are checked with Origin/Referer and Fetch Metadata headers, and all requests must use an allowed Host header.
- Path-scoped targets use `[scope].path_prefix`; initial inventory queries CDX with prefix matching, then dependency discovery reports linked first-party URLs that may need a follow-up dependency recovery pass before normalization can rewrite them locally.

## Scoped Recovery Notes

Path-scoped recovery starts with a prefix inventory: the first CDX query asks for the configured host or alias plus `[scope].path_prefix`. The dependency stage then inspects downloaded HTML/CSS and expands awareness to linked first-party URLs, including configured aliases and same-domain/subdomain first-party hosts.

A low CDX limit is a smoke scrape: useful for testing config, normalization, and preview safety. A complete scrape means exhausting or resuming CDX inventory, running dependency recovery for first-party missing requests, rerunning selection/download/dependencies/normalize/validate, and checking reports until missing first-party dependencies are acceptable or resolved.

If old-domain links remain in preview, do not assume publication is ready. They can be links hidden in scripts, unsupported attributes, externalized references, out-of-scope URLs, or first-party dependencies that have not been recovered yet. Inspect `reports/dependency-report.md`, `manifests/missing-dependency-requests.jsonl`, `reports/dependency-recovery-report.md`, `reports/normalization-report.md`, and validation output before widening scope or publishing.

## Pages

- `/` shows the dashboard, runs root, default config, recent runs, active count, and artifact count.
- `/targets` lists valid and invalid `configs/*.toml` files and includes target creation access.
- `/targets/new` creates a conservative browser-safe target config using the same defaults, TOML renderer, and validation as the CLI interview.
- `/runs` lists all runs under the selected runs root.
- `/runs` also has run initialization controls for known target configs.
- `/runs/<run_id>` shows run status, current stage, progress counts, stage readiness, gated stage controls, recent events, artifacts, object library access, and staging-site access.
- `/runs/<run_id>/objects` shows the unified object library for indexed run artifacts and manifest-referenced raw blobs.
- `/runs/<run_id>/objects/<object_id>` shows the unified object viewer with source, preview, download, and bytes actions when those modes are safe for the object type.
- `/runs/<run_id>/preview` wraps the private staging output in a trusted page with a sandboxed iframe.
- `/runs/<run_id>/site/` serves `staging/normalized-site/` for local inspection after normalization with a restrictive CSP.

## Browser Target And Run Workflow

1. Open `/targets/new` and enter the canonical domain, aliases, optional path prefix such as `/blog`, target mode, CDX limits, third-party policy, publication policy, and serving preference.
2. Submit the form to write `configs/<domain>.toml` or a simple custom `.toml` filename under `configs/`.
3. Open `/runs`, select the config, optionally enter a run ID, and initialize the run.
4. Open `/runs/<run_id>` and run stages in readiness order.
5. Inspect reports, artifacts, and indexed objects from the run page or `/runs/<run_id>/objects`, and preview normalized output through `/runs/<run_id>/preview` after `normalize` succeeds.

The equivalent JSON API flow is `GET /api/config/defaults`, optional `POST /api/config/validate`, `POST /api/configs`, then `POST /api/runs`.

## Starting Stages

From a run page, the UI can start these stages:

- `inventory`
- `select`
- `download`
- `dependencies`
- `dependency-recovery`
- `normalize`
- `validate`
- `captures-browser`

Only one stage may run for a run at a time. A started stage runs in a background thread in the current process. Standard output and errors are appended to `runs/<run_id>/logs/<stage>.log`; operator events are appended to `runs/<run_id>/logs/events.jsonl`; current state is written to `runs/<run_id>/ops/status.json`; the active lock is `runs/<run_id>/ops/stage-lock.json`.

Stage controls are gated by readiness metadata. A stage is ready only when the run has a frozen config path, no stage lock exists, and all required input artifacts for that stage exist. The `inventory` stage requires only the frozen run config; later stages require the manifests produced by earlier stages. The run page shows each stage's requirements, expected outputs, completion state, blocking reasons, and `ready` state.

Readiness requirements:

- `inventory`: frozen run config.
- `select`: `manifests/inventory.raw.jsonl`.
- `download`: `manifests/selection.pruned.jsonl`.
- `dependencies`: `manifests/selection.pruned.jsonl` and `manifests/download.results.jsonl`.
- `dependency-recovery`: `manifests/inventory.raw.jsonl` and `manifests/missing-dependency-requests.jsonl`.
- `normalize`: `manifests/selection.pruned.jsonl`, `manifests/inventory.canonical.jsonl`, and `manifests/download.results.jsonl`.
- `validate`: `manifests/site.manifest.jsonl` and non-empty `staging/normalized-site/`.
- `captures-browser`: `manifests/inventory.raw.jsonl`.

The web runner keeps options intentionally narrow. The visible run page exposes `inventory` `force` and `resume_key`; other stages use their pipeline defaults. The dependency recovery control warns that it appends first-party inventory rows and that operators should rerun `select`, `download`, `dependencies`, `normalize`, and `validate`. The normalize control warns that staging output is cleared before regenerated files are written.

## Direct Tailnet Staging Host

For a quick private link over the tailnet without Tailscale Serve or Funnel, serve the normalized staging directory directly on the machine's Tailscale IP:

```bash
archive-recovery serve-site --runs-root runs --run-id my-first-run --tailscale --port 18082
```

This prints a URL such as `http://100.x.y.z:18082/`. It serves only `staging/normalized-site` for that run and does not expose the operator web UI, manifests, raw blobs, logs, or reports. `archive-recovery serve-site --tailscale` binds directly to this machine's Tailscale IP; it does not configure Tailscale Serve or Funnel. Tailscale Serve proxies a local service through Tailscale configuration; Funnel can expose publicly and should remain off unless separately approved.

## Stage API Example

Example API start request:

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'X-CSRF-Token: <token-from-archive_recovery_csrf-cookie>' \
  -d '{"force": false, "csrf_token": "<token>"}' \
  http://127.0.0.1:18080/api/runs/my-first-run/stages/inventory
```

Use the same endpoint for any ready stage, including `dependency-recovery`; API callers receive `202` when the background job is queued and can poll `/api/runs/<run_id>/status`, `/api/runs/<run_id>/events`, and `/api/runs/<run_id>/stages` for completion and output state.

## Events, Status, Artifact, And Object APIs

- `GET /api/status` returns the runs root and summaries for known runs.
- `GET /api/configs` lists target configs under `configs/`.
- `GET /api/config/defaults` returns browser form defaults plus allowed target modes, third-party modes, publication policies, and serving preferences.
- `POST /api/config/validate` validates either an existing `config_path` or a proposed config payload rendered to TOML.
- `POST /api/configs` writes a validated target config under `configs/` and returns its summary.
- `POST /api/runs` initializes a run from `config_path`, optional `run_id`, and optional `force=true`.
- `GET /api/runs/<run_id>` returns run detail, frozen config details, status, artifacts, and stage readiness.
- `GET /api/runs/<run_id>/status` returns the run state, current stage, event count, and metrics.
- `GET /api/runs/<run_id>/stages` returns stage requirements, outputs, completion state, blockers, and `ready` flags.
- `GET /api/runs/<run_id>/events?limit=200` returns recent events from `logs/events.jsonl`; the limit is clamped between 1 and 2000.
- `GET /api/runs/<run_id>/events/stream` streams server-sent `progress` events for the run page.
- `GET /api/runs/<run_id>/artifacts` lists files under `config`, `manifests`, `reports`, `logs`, `ops`, CDX/capture-browser outputs, staging output, and indexed raw blob references with size, modified time, kind, category, and inferred stage when available.
- `GET /api/runs/<run_id>/objects` returns the indexed object library. Categories include `manifests`, `reports`, `logs`, `config`, `ops`, `cdx`, `staging`, and raw content-addressed blobs referenced by manifests.
- `GET /api/runs/<run_id>/objects` returns the indexed object library. Query parameters include `limit`, `offset`, `kind`, `stage`, `preview`, `renderer`, and `q`.
- `GET /api/runs/<run_id>/objects/<object_id>` returns object metadata, category, size, modified time, MIME hints, renderer/schema hints, manifest provenance when known, and available safe viewer modes.
- `GET /api/runs/<run_id>/objects/<object_id>/rows` returns paginated JSONL or external-links table rows.
- `GET /api/runs/<run_id>/objects/<object_id>/json` returns parsed JSON for small JSON objects.
- `GET /api/runs/<run_id>/objects/<object_id>/hex` returns a bounded hex/ascii byte sample for binary inspection.
- `GET /api/runs/<run_id>/objects/<object_id>/source` returns text-like content as inert source for review.
- `GET /api/runs/<run_id>/objects/<object_id>/preview` returns a constrained preview for object types that can be viewed safely without executing archived code.
- `GET /api/runs/<run_id>/objects/<object_id>/download` returns the object as an attachment.
- `GET /api/runs/<run_id>/objects/<object_id>/bytes` returns raw bytes for tools and diagnostics.
- `POST /api/runs/<run_id>/stages/<stage>` starts a gated stage and returns `202` JSON for API callers or redirects back to the run page for browser form posts.
- `GET /runs/<run_id>/artifacts/<path>` serves a listed artifact file.
- `GET /runs/<run_id>/reports/<path>` serves a report file from `reports`.
- `GET /runs/<run_id>/objects` serves the object library page.
- `GET /runs/<run_id>/objects/<object_id>` serves the unified object viewer page.

Status metrics are derived from known manifests and reports, including inventory records, selected captures, download results, dependency records, missing dependency requests, normalized files, report count, staging file count, and external-link count when available.

## Unified Object Library And Viewer

The object library is the preferred way to inspect run outputs because it presents filesystem artifacts and manifest-linked blobs through one indexed model instead of separate report/artifact links. It indexes:

- `manifests`: JSONL and JSON outputs that connect pipeline stages.
- `reports`: validation, selection, download, dependency, normalization, capture-browser, and other generated reports.
- `logs`: stage logs and event streams.
- `config`: frozen run config and related config artifacts.
- `ops`: status, lock, and operator state files.
- `cdx`: CDX and capture-browser inventory artifacts when present.
- `staging`: normalized-site files generated for local inspection.
- Raw blobs referenced by manifests: content-addressed source bytes stored under raw storage and connected back to selection/download/site manifests when the index can resolve them.

Viewer modes are deliberately separate:

- `source` is for text-oriented inspection and renders content as inert source.
- `preview` is only for object types that can be represented safely without executing archived scripts.
- `download` serves an attachment for local tools or manual review.
- `bytes` serves raw object bytes for diagnostics and scripted consumers.

Archived HTML and JavaScript are not executed in the object viewer. HTML source may be displayed as text, and bytes may be downloaded, but the viewer does not mount archived HTML/JS as active same-origin application content. Use `/runs/<run_id>/preview` for the normalized staging-site preview after reviewing the run's safety and privacy posture.

## Noindex Staging Responses

- The web app adds `X-Robots-Tag: noindex, noarchive` to every response by default.
- Staging-site preview responses from `/runs/<run_id>/site/` also set `X-Robots-Tag: noindex, noarchive` explicitly.
- These headers reduce accidental indexing if a local or tailnet service is exposed, but they are not an access-control mechanism and do not make public exposure safe.

## Safety Guardrails

- The default host is `127.0.0.1`; non-local binding is blocked unless `--allow-nonlocal` is provided.
- Non-loopback startup requires auth unless `--unsafe-no-auth` is explicitly used. Auth can be supplied by bearer token, auth cookie, or a one-time `?token=` visit that sets the cookie.
- Unsafe methods require CSRF tokens unless authenticated with an `Authorization: Bearer ...` API request.
- Tailscale access is private to the tailnet, but it still exposes local run metadata to tailnet peers that can reach the service.
- Browser target creation is limited to simple filenames under `configs/`; run IDs and artifact paths are still validated separately.
- Browser run initialization rejects configs whose `paths.runs_root` does not match the web process runs root.
- Stage readiness blocks premature stage starts and stage locks block concurrent stages, but operators should still inspect failures before retrying or forcing reruns.
- Run IDs cannot contain path separators and must resolve under the configured runs root.
- Artifact, report, and staging-site file paths are resolved under their allowed roots to reject traversal and symlink escapes.
- Object IDs and object file paths are resolved through the object index and allowed roots to reject traversal and symlink escapes.
- The UI serves existing local run artifacts only. Do not publish `runs/`, `raw/`, `data/`, manifests, logs, reports, or status files.
- The object viewer does not execute archived HTML or JavaScript; source and preview modes are inspection tools, not a replay browser.
- `X-Robots-Tag: noindex, noarchive` is a fallback header, not an authorization boundary.
- Public promotion remains a separate approval concern. Treat the web UI as private operator tooling until validation and privacy review pass.
- Third-party recovery and publication policy still come from the target config and pipeline behavior; the web UI does not relax those controls.

## Remaining Limitations And Next Steps

- Object indexing depends on artifacts and manifests already written by completed stages; incomplete or failed stages may leave gaps.
- Raw blob discovery is limited to blobs referenced by known manifests, not every file that may exist under raw storage.
- Preview support is intentionally conservative and should expand by MIME/type allowlist rather than by executing archived content.
- The object library is still private operator tooling and does not replace validation, privacy review, promotion, or publication gates.
- Additional tests should cover object indexing, safe mode selection, path containment, MIME handling, and manifest-to-blob provenance.

## Troubleshooting

- `web UI requires optional dependencies`: install with `python -m pip install -e '.[web]'`.
- `web UI defaults to local-only`: use the default loopback host or pass `--allow-nonlocal` deliberately with a non-loopback `--host`.
- `non-loopback web UI requires --auth-token`: pass `--auth-token` or `--auth-token-file`, or do not bind outside loopback.
- `CSRF token required`: refresh a web page to set the CSRF cookie, then submit forms normally or include the cookie value in `csrf_token`/`X-CSRF-Token` for API calls.
- `config path is required for this run`: pass `--config configs/<domain>.toml`, or initialize the run with `archive-recovery init --config ... --run-id ...` so a frozen config path is available.
- `config paths.runs_root (...) does not match web runs root (...)`: restart the web UI with the matching `--runs-root`, or edit/create a config whose `paths.runs_root` matches the web process.
- `stage <name> is not ready`: check `/api/runs/<run_id>/stages` or the run page readiness timeline for missing manifests, missing frozen config, or an active stage lock.
- `another stage is already running`: wait for the active stage to finish, then refresh the run page or check `/api/runs/<run_id>/status`.
- `staging site not found`: run `normalize` successfully before opening `/runs/<run_id>/preview` or `/runs/<run_id>/site/`.
- `object not found`: refresh the run page or object library after the producing stage finishes; if the object is a raw blob, confirm the manifest references it.
- `preview is unavailable`: use source, download, or bytes mode; archived HTML/JS is intentionally not executed in the object viewer.
- A stage failed with little detail on the page: inspect `runs/<run_id>/logs/<stage>.log` and `runs/<run_id>/ops/status.json`.
- Events are not updating: refresh the run page, then check `runs/<run_id>/logs/events.jsonl`; the browser stream polls the local file every few seconds.
