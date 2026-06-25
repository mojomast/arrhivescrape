# arrhivescrape

Planning artifacts for recovering historical `kyledurepos.com` content from the Internet Archive Wayback Machine, deduplicating it, and serving the static mirror locally and through Tailscale at `pwned.ussyco.de`.

This repository is documentation-first. It contains research notes, competing implementation specifications, tournament-style reviews, and one final authoritative build specification.

## File Guide

| File | Purpose |
| --- | --- |
| `FINAL-SPEC.md` | The final authoritative build document. It synthesizes the research, compares the proposed designs, selects the recommended architecture, and provides the complete end-to-end implementation plan. Start here. |
| `research-cdx-api.md` | Research on the Wayback CDX Server API, including query parameters, `collapse=digest`, `resumeKey` pagination, field selection, rate limits, and mandatory `id_` capture fetch URLs. |
| `research-tooling.md` | Comparison of recovery/download tooling such as `waybackpack`, `wget --mirror`, Python `wayback`, `internetarchive`, and Scrapy-based approaches. |
| `research-hosting.md` | Research on static hosting options for the recovered mirror, including nginx, Caddy, MIME handling, rewrite behavior, directory index behavior, and Tailscale Serve/Funnel integration. |
| `research-dedup.md` | Research on deduplication and post-processing, including CDX digest deduplication, SHA256 on-disk checks, URL normalization, artifact stripping, snapshot selection, and file tree layout. |
| `research-orchestration.md` | Research on pipeline automation, including Python `asyncio`/`httpx`, SQLite WAL checkpointing, rate-limited worker patterns, exponential backoff, logging, Docker, and virtualenv tradeoffs. |
| `spec-minimalist.md` | Candidate implementation spec using `waybackpack`, shell scripts, SQLite tracking, nginx, and Tailscale Serve. Optimized for the fewest dependencies and fastest setup. |
| `spec-pythonic-async.md` | Candidate implementation spec using a custom Python async pipeline with `httpx`, `asyncio`, SQLite WAL state, Caddy, and Tailscale integration. This became the primary basis for the final spec. |
| `spec-containerized.md` | Candidate implementation spec using Docker Compose services for CDX crawling, downloading, deduplication, static serving, and Tailscale sidecar networking. |
| `review-reliability.md` | Tournament review of the three candidate specs focused on correctness, rate limiting, retry behavior, deduplication accuracy, resumability, `id_` usage, and binary handling. |
| `review-dx.md` | Tournament review of the three candidate specs focused on developer experience, debuggability, progress visibility, extensibility, output cleanliness, and time-to-first-run. |
| `review-production.md` | Tournament review of the three candidate specs focused on serving robustness, HTTPS, MIME/cache behavior, security posture, Tailscale integration, and incremental updates. |

## Required Recovery Constraints

The final plan preserves these non-negotiable constraints:

- Use CDX `collapse=digest` during discovery.
- Run an additional SHA256 deduplication pass on downloaded files.
- Use the Wayback `id_` modifier on every content fetch URL.
- Keep CDX API traffic at or below 1 request per second with exponential backoff on `429` responses.
- Recover static output only: HTML, CSS, JavaScript, images, fonts, and documents.
- Serve the mirror through Tailscale for `pwned.ussyco.de`.

## Suggested Reading Order

1. `FINAL-SPEC.md`
2. `review-reliability.md`, `review-dx.md`, and `review-production.md`
3. `spec-pythonic-async.md`, `spec-minimalist.md`, and `spec-containerized.md`
4. The five `research-*.md` files for source context
