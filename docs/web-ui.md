# Local Web UI

The web UI is an optional local operator console for Archive Recovery Toolkit runs. It uses the same pipeline functions as the CLI and reads/writes the normal ignored run directories; it does not replace the CLI or publish recovered sites.

## Install And Start

Install the optional web dependencies from the repo root:

```bash
python -m pip install -e '.[web]'
```

Create a target config and initialize a run before using stage controls:

```bash
archive-recovery new --domain example.com --non-interactive
archive-recovery init --config configs/example.com.toml --run-id my-first-run
```

Start the local dashboard:

```bash
archive-recovery web --runs-root runs --config configs/example.com.toml
```

Open `http://127.0.0.1:18080/`. The default bind is loopback-only. To bind outside loopback, pass both a non-local `--host` and `--allow-nonlocal` intentionally.

For private tailnet access, prefer a local web process plus an explicit Tailscale-only exposure. Keep it off the public internet unless the target has passed validation and privacy review. One direct tailnet option is:

```bash
TAILSCALE_IP=$(tailscale ip -4)
archive-recovery web --runs-root runs --config configs/example.com.toml --host "$TAILSCALE_IP" --port 18080 --allow-nonlocal
```

Then open `http://<tailscale-ip>:18080/` from another device in the same tailnet. If using `tailscale serve`, keep the target local-only and verify the route before sharing it:

```bash
archive-recovery web --runs-root runs --config configs/example.com.toml --port 18080
tailscale serve --bg --yes http://127.0.0.1:18080
tailscale serve status
```

## Local Operation Model

- The app is served by `uvicorn` and the optional Starlette/Jinja2 web package.
- `--runs-root` selects the run directory root to browse; default is `runs`.
- `--config` provides a default TOML config for starting stages when the run does not already have a frozen config path.
- Run config, manifests, reports, logs, and status stay under the existing ignored run directory layout.
- Stage output is produced by the same package pipeline modules used by `archive-recovery inventory`, `select`, `download`, `dependencies`, `normalize`, `validate`, and `captures-browser`.

## Pages

- `/` shows the dashboard, runs root, default config, recent runs, active count, and artifact count.
- `/targets` lists valid and invalid `configs/*.toml` files and shows the matching `archive-recovery init` command.
- `/targets/new` points operators back to the CLI interview for conservative config creation.
- `/runs` lists all runs under the selected runs root.
- `/runs/<run_id>` shows run status, current stage, progress counts, stage controls, recent events, artifacts, and staging-site access.
- `/runs/<run_id>/site/` serves `staging/normalized-site/` for local inspection after normalization.

## Starting Stages

From a run page, the UI can start these stages:

- `inventory`
- `select`
- `download`
- `dependencies`
- `normalize`
- `validate`
- `captures-browser`

Only one stage may run for a run at a time. A started stage runs in a background thread in the current process. Standard output and errors are appended to `runs/<run_id>/logs/<stage>.log`; operator events are appended to `runs/<run_id>/logs/events.jsonl`; current state is written to `runs/<run_id>/ops/status.json`.

The web runner keeps options intentionally narrow. The `inventory` stage accepts JSON options for `force` and `resume_key`; other stages use their pipeline defaults.

Example API start request:

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"force": false}' \
  http://127.0.0.1:18080/api/runs/my-first-run/stages/inventory
```

## Events, Status, And Artifact APIs

- `GET /api/status` returns the runs root and summaries for known runs.
- `GET /api/runs/<run_id>/status` returns the run state, current stage, event count, and metrics.
- `GET /api/runs/<run_id>/events?limit=200` returns recent events from `logs/events.jsonl`; the limit is clamped between 1 and 2000.
- `GET /api/runs/<run_id>/events/stream` streams server-sent `progress` events for the run page.
- `GET /api/runs/<run_id>/artifacts` lists files under `config`, `manifests`, `reports`, `logs`, and `ops` with size, modified time, kind, and inferred stage.
- `GET /runs/<run_id>/artifacts/<path>` serves a listed artifact file.
- `GET /runs/<run_id>/reports/<path>` serves a report file from `reports`.

Status metrics are derived from known manifests and reports, including inventory records, selected captures, download results, dependency records, missing dependency requests, normalized files, report count, staging file count, and external-link count when available.

## Safety Guardrails

- The default host is `127.0.0.1`; non-local binding is blocked unless `--allow-nonlocal` is provided.
- Tailscale access is private to the tailnet, but it still exposes local run metadata to tailnet peers that can reach the service.
- Run IDs cannot contain path separators and must resolve under the configured runs root.
- Artifact, report, and staging-site file paths are resolved under their allowed roots to reject traversal and symlink escapes.
- The UI serves existing local run artifacts only. Do not publish `runs/`, `raw/`, `data/`, manifests, logs, reports, or status files.
- Public promotion remains a separate approval concern. Treat the web UI as private operator tooling until validation and privacy review pass.
- Third-party recovery and publication policy still come from the target config and pipeline behavior; the web UI does not relax those controls.

## Troubleshooting

- `web UI requires optional dependencies`: install with `python -m pip install -e '.[web]'`.
- `web UI defaults to local-only`: use the default loopback host or pass `--allow-nonlocal` deliberately with a non-loopback `--host`.
- `config path is required for this run`: pass `--config configs/<domain>.toml`, or initialize the run with `archive-recovery init --config ... --run-id ...` so a frozen config path is available.
- `another stage is already running`: wait for the active stage to finish, then refresh the run page or check `/api/runs/<run_id>/status`.
- `staging site not found`: run `normalize` successfully before opening `/runs/<run_id>/site/`.
- A stage failed with little detail on the page: inspect `runs/<run_id>/logs/<stage>.log` and `runs/<run_id>/ops/status.json`.
- Events are not updating: refresh the run page, then check `runs/<run_id>/logs/events.jsonl`; the browser stream polls the local file every few seconds.
