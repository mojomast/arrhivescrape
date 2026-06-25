# Python Async Recovery Spec

This is the preferred implementation option for medium and large recoveries.

## Shape

- Python CLI command: `archive-recovery`.
- Interactive setup command: `archive-recovery new`.
- Async CDX and content workers with bounded concurrency.
- SQLite WAL state for resumability.
- JSONL manifests and logs for streaming auditability.
- TOML target config and frozen per-run JSON config.

## Why This Option

The async design gives precise rate limiting, durable retries, structured progress, reusable normalization code, and better handling for mixed HTML, binary assets, aliases, and dependency passes than shell-only mirroring.

## Default Stages

`new`, `inventory`, `select`, `download`, `dependencies`, `normalize`, `validate`, `privacy`, `promote`, and `serve`.

## Serving

Generate serving files under `runs/<run_id>/ops/`. Caddy is the default local static server because it is concise and handles MIME types well. Tailscale and public serving are optional policy-controlled modes.
