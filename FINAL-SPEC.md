# Final Spec: Generic Wayback Static-Site Recovery

## Summary

This project builds a reusable pipeline for recovering archived websites and forums from Wayback/CDX into static output. It is config-driven, target-neutral, resumable, privacy-aware, and designed to keep generated artifacts out of source control.

## Architecture

```text
Internet Archive CDX
  -> inventory and alias discovery
  -> capture selection
  -> Wayback id_ downloads
  -> raw SHA256 store
  -> normalization and link rewriting
  -> validation and privacy review
  -> recovered/<domain>/releases/<run_id>/site
  -> optional local, tailnet, or public serving
```

## Required Behavior

- Discover captures through CDX using `collapse=digest` for the primary pass.
- Preserve alias information with a supplemental uncollapsed inventory when configured.
- Fetch content with `https://web.archive.org/web/{timestamp}id_/{original_url}`.
- Rate-limit CDX traffic to one request at a time with at least `1.1` seconds between starts by default.
- Retry `429` and transient errors with exponential backoff and `Retry-After` support.
- Store raw bytes under `raw/sha256/` and normalized output under a run staging directory.
- Use SQLite or equivalent durable state for cursors, captures, jobs, retries, outputs, and validation status.
- Keep generated data under ignored directories: `data/`, `raw/`, `runs/`, `logs/`, and `recovered/`.
- Block public publication until validation and privacy review approve the requested policy.

## Configuration Model

Human-authored target config lives at `configs/<domain>.toml`. Each run freezes a normalized copy at `runs/<run_id>/config/run-config.json`.

Important sections:

- `[scope]`: canonical domain, aliases, and scope mode.
- `[target]`: `latest-good`, `date-specific`, `full-captures`, or `selected-eras`.
- `[cdx]`: endpoint, filters, fields, pagination, collapse, and alias inventory.
- `[rate_limits]`: CDX and content worker limits.
- `[content]`: MIME classes, Wayback fetch modifier, and active JavaScript policy.
- `[third_party]`: off, audit-only, capped recovery, or approved full recovery.
- `[paths]`: data, raw, run, staging, release, and promoted output paths.
- `[privacy]`: publication intent and blocking rules.
- `[serving]`: Caddy/Tailscale/public serving preference.

## Pipeline Stages

1. `new`: interactive interview that writes config and scaffolds a run.
2. `inventory`: CDX discovery with pagination, aliases, and durable cursor state.
3. `select`: choose captures based on mode, MIME class, timestamp, and URL quality.
4. `download`: fetch selected captures through Wayback `id_` URLs into `raw/sha256/`.
5. `dependencies`: inspect downloaded HTML/CSS for unresolved first-party and optional third-party references.
6. `normalize`: build a static file tree, rewrite links, neutralize configured forms, and remove replay artifacts.
7. `validate`: check MIME mismatches, broken links, missing assets, privacy blockers, and static serving behavior.
8. `promote`: copy or link an approved static site into `recovered/<domain>/releases/<run_id>/site`.
9. `serve`: generate local, tailnet, or public serving configuration when allowed by policy.

## Output Contract

Tracked source contains code, specs, and templates only. Run evidence, raw downloads, SQLite files, logs, generated reports, operational Caddy/Tailscale/nginx files, and static output are local artifacts and must remain ignored.
