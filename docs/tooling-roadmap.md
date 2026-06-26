# Tooling Roadmap

This project is becoming a complete Wayback/static-site recovery suite by reusing the working recovery scripts that already succeeded, not by reinventing the pipeline from scratch.

The current `archive_recovery` package now has the generic setup/interview command, run initialization, migrated core pipeline stages, report generation, and an optional local web frontend foundation. Remaining work should keep promoting proven behavior into reusable package modules, remove target-specific assumptions from core, and preserve the same staged workflow.

## Completed Foundation

- Generic target setup and run initialization with frozen run configs.
- Shared config loading, run context/path handling, JSONL helpers, state helpers, Wayback/CDX access, URL normalization, MIME helpers, and content-addressed storage.
- Migrated package stages for CDX inventory, capture selection, downloads, dependency discovery, static normalization, validation, and capture-browser generation.
- CLI commands for `new`, `init`, `validate-config`, `inventory`, `select`, `download`, `dependencies`, `normalize`, `validate`, `captures-browser`, and `web`.
- Optional local web UI foundation with dashboard, targets, runs, run detail, stage controls, live events, status/artifact APIs, and staging-site preview.

## Reuse Principle

Keep the behavior that worked:

- CDX inventory with conservative rate limiting and resume state.
- Capture selection from CDX inventory.
- Wayback `id_` downloads.
- Raw SHA256 content-addressed storage.
- Dependency discovery from HTML/CSS.
- Static normalization and link rewriting.
- MIME and broken-link reporting.
- Capture browser generation.
- Optional forum/phpBB repair passes as plugins.

Change only what prevents reuse:

- Replace hardcoded domains with config values.
- Replace hardcoded run IDs with `--run-id` or config-derived paths.
- Replace hardcoded local paths with `RunContext` paths.
- Move generated reports/logs/state under ignored run directories.
- Move forum-specific assumptions out of core and into plugins.

## Migrated Pipeline Modules

| Original source | Package module | Status | Notes |
| --- | --- | --- | --- |
| Setup/interview workflow | `archive_recovery/cli.py`, `archive_recovery/config.py`, `archive_recovery/context.py` | Complete | Writes target TOML, initializes run directories, and freezes normalized run config. |
| CDX inventory workflow | `archive_recovery/pipeline/inventory.py` | Complete | Uses config-driven CDX endpoint, filters, aliases, pagination/resume state, rate limits, and run manifests. |
| `tools/run_selection.py` | `archive_recovery/pipeline/selection.py` | Complete | Migrated capture selection, canonical inventory output, route/content classification, selected manifest, and selection report. |
| `tools/run_download.py` | `archive_recovery/pipeline/download.py` | Complete | Migrated Wayback `id_` downloads, retries/backoff, raw SHA256 storage, result manifest, and download report. |
| `tools/run_dependencies.py` | `archive_recovery/pipeline/dependencies.py` | Complete | Migrated HTML/CSS dependency extraction, dependency graph, missing first-party requests, and report output. |
| `tools/run_normalization.py` | `archive_recovery/pipeline/normalization.py` | Complete | Migrated output path mapping, Wayback artifact stripping, HTML/CSS rewriting, collision handling, site manifest, normalization report, and MIME audit. |
| Validation/report pass | `archive_recovery/pipeline/validation.py` | Complete | Adds staging-site link/reference checks, MIME warnings, validation report, and external-link report. |
| `tools/build_capture_browser.py` | `archive_recovery/pipeline/captures_browser.py` | Complete | Migrated static capture browser generation under run reports. |

## Completed Web Frontend Foundation

| Area | Status | Notes |
| --- | --- | --- |
| Optional dependencies | Complete | `web` extra installs Starlette, Jinja2, and uvicorn without making them core dependencies. |
| CLI entry point | Complete | `archive-recovery web` serves the local dashboard with configurable runs root, default config, host, and port. |
| Local safety | Complete | Defaults to loopback and requires `--allow-nonlocal` for non-loopback binds. |
| Pages | Complete | Dashboard, targets, new-target guide, runs index, run detail, artifact list, events, metrics, and staging-site preview. |
| Stage runner | Complete | Starts one stage per run in-process, records status in `ops/status.json`, events in `logs/events.jsonl`, and logs in `logs/<stage>.log`. |
| APIs | Complete | Exposes status, events, event stream, artifacts, stage start, reports, artifacts, and staging-site file routes. |

## Existing Scripts To Turn Into Plugins

| Existing local script | Promote to | Reuse level | Notes |
| --- | --- | --- | --- |
| `tools/fix_forum_images.py` | `archive_recovery/plugins/phpbb/images.py` | Medium-high | Preserve phpBB/subSilver asset repair and placeholder reporting. Configure forum root, theme, asset roots, and first-party hosts. |
| `tools/fix_forum_navigation.py` | `archive_recovery/plugins/phpbb/navigation.py` | Medium-high | Preserve static phpBB route repair. Configure forum root, route names, title prefix, and archive index naming. |
| `tools/wire_forum_archive.py` | `archive_recovery/plugins/phpbb/archive_index.py` | Medium-high | Preserve unreachable-page discovery and archive index generation. Make labels and routes configurable. |
| `tools/recover_forum_media_wayback.py` | `archive_recovery/plugins/phpbb/media.py` or generic `recover-media` | Medium | Preserve exact first-party media recovery. Parameterize hosts, scan roots, caps, paths, and reports. |
| `tools/recover_forum_external_media.py` | `archive_recovery/pipeline/third_party.py` plus phpBB integration | Medium | Preserve capped external media recovery, but gate behind privacy/config policy. |
| `tools/replace_phpbb_assets.py` | `archive_recovery/plugins/phpbb/assets.py` | Medium | Preserve stock phpBB asset restoration. Replace shell/external unzip with Python `zipfile` if practical. |

## Scripts To Keep As Case Study Only

| Existing local script | Recommendation | Reason |
| --- | --- | --- |
| `tools/publish_pwnedforums.py` | Keep local/case-study only | It hardcodes one public destination, prefix, and publication workflow. Implement generic `promote`/`publish` separately with privacy gates. |
| `tools/inventory_dependencies_feedback_2.py` | Mine for logic, do not promote directly | It has useful focused-dependency ideas but patches one run and contains target/forum-specific alias rules. |

## Target Package Shape

```text
archive_recovery/
  cli.py
  config.py
  context.py
  jsonl.py
  paths.py
  state.py
  wayback.py
  cdx.py
  urlnorm.py
  mime.py
  storage.py
  pipeline/
    inventory.py
    selection.py
    download.py
    dependencies.py
    normalization.py
    validation.py
    promote.py
  reports/
    markdown.py
    broken_links.py
  web/
    app.py
    jobs.py
    fs.py
  plugins/
    base.py
    phpbb/
      images.py
      navigation.py
      archive_index.py
      assets.py
      media.py
```

## CLI Commands To Build From Existing Scripts

```bash
archive-recovery new
archive-recovery init --config configs/example.com.toml
archive-recovery validate-config --config configs/example.com.toml
archive-recovery inventory --config configs/example.com.toml --run-id RUN_ID
archive-recovery select --config configs/example.com.toml --run-id RUN_ID
archive-recovery download --config configs/example.com.toml --run-id RUN_ID
archive-recovery dependencies --config configs/example.com.toml --run-id RUN_ID
archive-recovery normalize --config configs/example.com.toml --run-id RUN_ID
archive-recovery validate --config configs/example.com.toml --run-id RUN_ID
archive-recovery captures-browser --config configs/example.com.toml --run-id RUN_ID
archive-recovery web --runs-root runs --config configs/example.com.toml
archive-recovery promote --run-id RUN_ID
archive-recovery serve --run-id RUN_ID
archive-recovery phpbb fix-images --run-id RUN_ID
archive-recovery phpbb fix-navigation --run-id RUN_ID
archive-recovery phpbb wire-archive --run-id RUN_ID
```

## Completed Implementation Order

1. Added shared `RunContext`, config loader, path resolver, JSONL helpers, and state helpers.
2. Migrated CDX inventory into a package stage.
3. Migrated selection with minimal behavior changes.
4. Migrated download with raw content-addressed storage and report output.
5. Migrated dependency discovery.
6. Migrated normalization.
7. Added validation/report aggregation around existing run artifacts.
8. Migrated capture-browser generation.
9. Added the optional local web frontend foundation.

## Next Steps

1. Add focused tests for URL normalization, output path mapping, MIME classification, Wayback error detection, dependency extraction, link rewriting, validation, and web path-safety helpers.
2. Decide whether the dependency inventory feedback pass should return as a generic package stage or remain folded into targeted iteration workflows.
3. Add generic `promote` and `serve` commands with explicit validation/privacy gates before any public output path is written.
4. Promote phpBB/forum repair scripts into plugins without hardcoded target paths.
5. Add stage cancellation or clearer queued/running lifecycle controls for the local web UI if long-running operator sessions need it.
6. Add optional web controls for safe stage-specific parameters beyond inventory `force` and `resume_key` only when the CLI behavior is stable.
7. Keep generated artifacts, raw data, logs, run directories, SQLite databases, and promoted site output ignored by git.

## Best-Practice Constraints

- Use Wayback CDX as inventory, not recursive crawling as the source of truth.
- Use `id_` replay URLs for downloaded source bytes.
- Keep CDX rate limits conservative and retry with `Retry-After` support.
- Preserve raw bytes separately from normalized output.
- Treat third-party recovery as opt-in or audit-only by default.
- Keep every rewrite and selected capture traceable through manifests.
- Block public promotion until validation and privacy policy pass.

## Non-Goals For The Core

- Do not depend on a replay server like pywb for normal static output.
- Do not make browser automation required for MVP.
- Do not make Docker required for normal use.
- Do not pull entire third-party dependency graphs by default.
- Do not put target-specific publication scripts in core.
