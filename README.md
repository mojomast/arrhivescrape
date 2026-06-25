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

Use the built-in CLI directly from the repo:

```bash
python -m archive_recovery new
```

For a scripted setup:

```bash
python -m archive_recovery new --domain example.com --non-interactive
```

This writes `configs/example.com.toml` and creates a scaffolded `runs/<run_id>/` directory.

## Configure A Target

The interview asks for canonical domain, aliases, target mode, Wayback/CDX settings, rate limits, third-party asset policy, output paths, privacy/publication policy, and Caddy/Tailscale/public serving preference. The generated TOML is human-editable, and each run freezes a normalized JSON copy into `runs/<run_id>/config/run-config.json`.

## Validation And Publication

Validation should block promotion when downloads are invalid, static links are broken beyond the configured threshold, MIME classes are wrong, forms or sensitive query parameters remain in a public build, or the privacy review has not approved the requested publication mode.

Publication is opt-in. Local and tailnet serving can use generated Caddy/Tailscale configuration under the run directory. Public serving should require explicit approval and a privacy policy such as `public-noindex` or `public-indexable`.

## Planning Docs

Start with the planning index: [`docs/planning-index.md`](docs/planning-index.md).

The original tool was designed with a staged agent workflow: parallel research agents, parallel competing design agents, parallel review/judge agents, and a final synthesis agent. The historical workflow and prompts are preserved in [`docs/archive/original-planning/workflow.md`](docs/archive/original-planning/workflow.md).

- [`FINAL-SPEC.md`](FINAL-SPEC.md) is the generic authoritative build spec.
- [`spec-pythonic-async.md`](spec-pythonic-async.md) describes the preferred async implementation.
- [`spec-minimalist.md`](spec-minimalist.md) and [`spec-containerized.md`](spec-containerized.md) document alternate implementation options.
- `research-*.md` files summarize CDX, tooling, hosting, deduplication, and orchestration research.
- `review-*.md` files capture reliability, developer experience, and production readiness tradeoffs.
