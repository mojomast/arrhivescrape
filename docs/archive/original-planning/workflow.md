# How This Tool Was Designed

This project was designed with a staged, agent-assisted workflow rather than a single linear planning pass. The goal was to turn a one-off archived-site recovery problem into a reusable recovery toolkit by separating research, design, review, and synthesis.

## Workflow Summary

1. Five research agents ran in parallel to investigate the problem space.
2. Three design agents ran in parallel to produce competing build specs.
3. Three review agents ran in parallel to judge the designs from different perspectives.
4. One synthesis agent combined the strongest parts into the final implementation spec.
5. The actual recovery run was tracked separately in a progress log.

This made the design process more adversarial and evidence-based. Each stage produced markdown artifacts so later stages could critique, compare, and reuse the earlier work.

## Phase 0: Parallel Research

The first phase launched five research agents at the same time. Each agent owned one domain of the recovery problem:

| Agent | Output | Research area |
| --- | --- | --- |
| `R1` | [`research-cdx-api.md`](research-cdx-api.md) | Wayback CDX API, fields, pagination, `collapse=digest`, rate limits, and `id_` capture URLs. |
| `R2` | [`research-tooling.md`](research-tooling.md) | Existing tools such as `waybackpack`, `wget`, Python libraries, `internetarchive`, and Scrapy. |
| `R3` | [`research-hosting.md`](research-hosting.md) | Static hosting with Caddy/nginx, MIME handling, rewrites, directory indexes, and Tailscale exposure. |
| `R4` | [`research-dedup.md`](research-dedup.md) | CDX digest deduplication, SHA256 deduplication, URL normalization, and post-processing. |
| `R5` | [`research-orchestration.md`](research-orchestration.md) | Async orchestration, SQLite WAL state, retries, structured logs, Docker, and virtualenv tradeoffs. |

## Phase 1: Parallel Design Specs

The second phase launched three design agents at the same time. Each read all five research docs and wrote a complete implementation plan from a different architecture perspective:

| Agent | Output | Design approach |
| --- | --- | --- |
| `S1` | [`spec-minimalist.md`](spec-minimalist.md) | Minimal dependencies: shell scripts, `waybackpack`, SQLite tracking, nginx, and Tailscale. |
| `S2` | [`spec-pythonic-async.md`](spec-pythonic-async.md) | Custom Python async pipeline with HTTP workers, SQLite WAL state, Caddy, and structured reports. |
| `S3` | [`spec-containerized.md`](spec-containerized.md) | Docker Compose services for crawling, downloading, deduplication, serving, and Tailscale integration. |

The point was not to pick a favorite early. Each design had to be buildable and opinionated so the review phase had concrete tradeoffs to evaluate.

## Phase 2: Parallel Tournament Reviews

The third phase launched three review agents at the same time. Each reviewed all three specs plus the research docs, then scored the designs through a different lens:

| Agent | Output | Review lens |
| --- | --- | --- |
| `T1` | [`review-reliability.md`](review-reliability.md) | Correctness, rate limiting, retries, deduplication, resumability, `id_` usage, and binary handling. |
| `T2` | [`review-dx.md`](review-dx.md) | Debuggability, progress visibility, extensibility, output cleanliness, and time-to-first-run. |
| `T3` | [`review-production.md`](review-production.md) | Serving robustness, HTTPS, MIME/cache behavior, security posture, Tailscale integration, and updates. |

This was the tournament step. The reviews made the winning direction explicit instead of relying on gut feel.

## Phase 3: Final Synthesis

The synthesis agent read the research, the three specs, and the three reviews. It selected the Python async design as the primary architecture, then cherry-picked useful ideas from the other designs.

The result was [`FINAL-SPEC.md`](FINAL-SPEC.md), the original authoritative implementation plan.

## Execution Record

After the design workflow, the recovery itself was tracked in [`PROGRESS.md`](PROGRESS.md). That file was not part of the initial tournament. It records the actual run stages, validation decisions, privacy review, promotion, and later forum-specific work.

## Prompt Evidence

The exact prompts used for each research, design, review, and synthesis agent are preserved in [`README.md`](README.md). That file also records the original opencode session, prompt part IDs, timestamps, and first planning commit.
