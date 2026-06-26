# Archive Recovery Toolkit

Archive Recovery Toolkit is a reusable Wayback/CDX static-site recovery toolkit. It helps discover archived captures, choose a recoverable snapshot strategy, download and deduplicate assets, normalize links into a static site, validate the output, and optionally prepare local, tailnet, or public publication.

## Why It Exists

Old sites, forums, blogs, and asset trees often survive only as fragmented Wayback captures. Browser replay is useful for inspection, but it is not a durable static copy. This project provides a repeatable pipeline for turning CDX inventory and archived capture bytes into an auditable static mirror with manifests, reports, privacy gates, and serving configuration.

Origin note: this project began while recovering the author's old forum at `kyledurepos.com` and fixing archived links, but the toolkit is generic and adaptable to other recovery targets.

## Pipeline

The normal flow is:

1. Interview a new target and write `configs/<domain>.toml`.
2. Initialize a run under `runs/<run_id>/` with a frozen `run-config.json`.
3. Query CDX with `collapse=digest`, pagination, aliases, and rate limits.
4. Select captures using the target mode: `latest-good`, date-specific, full captures, or selected eras.
5. Download content through Wayback `id_` replay URLs into `raw/sha256/`.
6. Normalize URLs, assets, forms, and internal links into `runs/<run_id>/staging/normalized-site/`.
7. Validate MIME types, broken links, privacy constraints, and static serving behavior.
8. Promote approved output to `recovered/<domain>/releases/<run_id>/site/` and optionally serve it.

Generated data, raw downloads, logs, run directories, SQLite databases, and promoted site output are intentionally ignored by git.

## Run It

Install the package from the repo. The core CLI has no web-server dependency; install the optional `web` extra when you want the local dashboard:

```bash
python -m pip install -e .
python -m pip install -e '.[web]'
```

Use the built-in CLI directly from the repo:

```bash
python -m archive_recovery new
```

For a scripted setup:

```bash
python -m archive_recovery new --domain example.com --non-interactive
```

This writes `configs/example.com.toml` and creates a scaffolded `runs/<run_id>/` directory.

Then initialize and run the staged recovery tools:

```bash
python -m archive_recovery init --config configs/example.com.toml --run-id my-first-run
python -m archive_recovery inventory --config configs/example.com.toml --run-id my-first-run
python -m archive_recovery select --config configs/example.com.toml --run-id my-first-run
python -m archive_recovery download --config configs/example.com.toml --run-id my-first-run
python -m archive_recovery dependencies --config configs/example.com.toml --run-id my-first-run
python -m archive_recovery normalize --config configs/example.com.toml --run-id my-first-run
python -m archive_recovery validate --config configs/example.com.toml --run-id my-first-run
python -m archive_recovery captures-browser --config configs/example.com.toml --run-id my-first-run
```

The same commands are available through the installed script as `archive-recovery ...`.

## Local Web UI

The optional web UI is a local operator console for existing run directories. It lists targets and runs, starts one pipeline stage at a time for a run, streams progress events, exposes status JSON, links generated artifacts, and serves the normalized staging site from `runs/<run_id>/staging/normalized-site/` for inspection.

Start it from the repo root after installing the `web` extra:

```bash
archive-recovery web --runs-root runs --config configs/example.com.toml
```

The default bind is `127.0.0.1:18080`. Non-loopback binding requires the explicit `--allow-nonlocal` flag.

For tailnet-only access, bind to a Tailscale IP with `--allow-nonlocal` or use `tailscale serve` against a loopback instance. Keep generated run data private and do not expose the dashboard publicly.

Key local endpoints:

- `GET /` shows the dashboard.
- `GET /targets` lists `configs/*.toml` target configs.
- `GET /runs` and `GET /runs/<run_id>` show run status, metrics, events, stage controls, and artifacts.
- `POST /api/runs/<run_id>/stages/<stage>` starts `inventory`, `select`, `download`, `dependencies`, `normalize`, `validate`, or `captures-browser`.
- `GET /api/status`, `/api/runs/<run_id>/status`, `/api/runs/<run_id>/events`, and `/api/runs/<run_id>/artifacts` provide machine-readable run state.
- `GET /runs/<run_id>/site/` previews the normalized staging site.

See [`docs/web-ui.md`](docs/web-ui.md) for operating details, safety guardrails, API notes, and troubleshooting.

The tracked suite is now built around migrated generic package modules for the main recovery pipeline, with optional local web operation layered on top. See [`docs/tooling-roadmap.md`](docs/tooling-roadmap.md) for completed work and next steps.

## Configure A Target

The interview asks for canonical domain, aliases, target mode, Wayback/CDX settings, rate limits, third-party asset policy, output paths, privacy/publication policy, and Caddy/Tailscale/public serving preference. The generated TOML is human-editable, and each run freezes a normalized JSON copy into `runs/<run_id>/config/run-config.json`.

## Validation And Publication

Validation should block promotion when downloads are invalid, static links are broken beyond the configured threshold, MIME classes are wrong, forms or sensitive query parameters remain in a public build, or the privacy review has not approved the requested publication mode.

Publication is opt-in. Local and tailnet serving can use generated Caddy/Tailscale configuration under the run directory. Public serving should require explicit approval and a privacy policy such as `public-noindex` or `public-indexable`.

## Planning Docs

Start with the planning index: [`docs/planning-index.md`](docs/planning-index.md).

For the local dashboard, see [`docs/web-ui.md`](docs/web-ui.md).

The original tool was designed with a staged agent workflow: parallel research agents, parallel competing design agents, parallel review/judge agents, and a final synthesis agent. The historical workflow and prompts are preserved in [`docs/archive/original-planning/workflow.md`](docs/archive/original-planning/workflow.md).

- [`FINAL-SPEC.md`](FINAL-SPEC.md) is the generic authoritative build spec.
- [`spec-pythonic-async.md`](spec-pythonic-async.md) describes the preferred async implementation.
- [`spec-minimalist.md`](spec-minimalist.md) and [`spec-containerized.md`](spec-containerized.md) document alternate implementation options.
- `research-*.md` files summarize CDX, tooling, hosting, deduplication, and orchestration research.
- `review-*.md` files capture reliability, developer experience, and production readiness tradeoffs.
