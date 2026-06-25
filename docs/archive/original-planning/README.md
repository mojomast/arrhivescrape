# Original Planning Archive

This directory preserves the project planning markdown from the original recovery workspace. These files are historical process artifacts: they show the research, competing specs, reviews, and final plan used during the first completed recovery.

The active project documentation remains generic. Historical files may mention the original target, local paths, run IDs, and deployment decisions because they are preserved for context rather than used as current configuration.

For a plain-English explanation of the workflow used to create the tool, start with [`workflow.md`](workflow.md).

| File | Historical purpose |
| --- | --- |
| `workflow.md` | Narrative explanation of the parallel research, design, review, and synthesis workflow. |
| `original-README.md` | Original repository guide and reading order. |
| `FINAL-SPEC.md` | Original final build specification. |
| `PROGRESS.md` | Original run progress notes. |
| `spec-pythonic-async.md` | Original preferred async implementation spec. |
| `spec-minimalist.md` | Original minimalist implementation option. |
| `spec-containerized.md` | Original containerized implementation option. |
| `research-*.md` | Original research notes. |
| `review-*.md` | Original review notes comparing implementation approaches. |

## Creation Session

These files were created in an opencode session that used a circular tournament workflow: parallel research agents, parallel design/spec agents, parallel review agents, and one final synthesis agent.

| Field | Value |
| --- | --- |
| Parent session | `ses_1128bee33ffe65MDpY5CfodHYI` |
| Start time | `2026-06-22T03:51:07Z` |
| Main prompt part | `prt_eed7411df0023dSz5fv85009ZR` |
| First planning commit | `91458a83b56e4be21abb9be3a9819e8c373889fb` |
| Commit time | `2026-06-22T04:07:02Z` |
| Commit message | `Add Wayback recovery planning docs` |

The initial user prompt described the orchestration mode this way:

```text
# OpenCode Prompt: Wayback Machine Site Recovery — kyledurepos.com
## GPT-5.5-fast | Maximum Parallel Subagent Orchestration

## ORCHESTRATION MODE: CIRCULAR TOURNAMENT PIPELINE

Run this as a 4-phase parallel pipeline using the maximum number of subagents. Fire all subagents within each phase simultaneously — never sequentially. Produce a markdown artifact for every agent output. Phase N+1 does not start until all Phase N artifacts are confirmed. You are the coordinator only — delegate all research and design work to subagents.
```

## Phase Flow

| Phase | Agents | Output |
| --- | --- | --- |
| Phase 0 research | `R1` through `R5`, launched together at `2026-06-22T03:51:30Z` | Five `research-*.md` files. |
| Phase 1 specs | `S1`, `S2`, `S3`, launched together at `2026-06-22T03:54:18Z` | Three competing `spec-*.md` designs. |
| Phase 2 reviews | `T1`, `T2`, `T3`, launched together at `2026-06-22T03:58:05Z` | Three tournament review files. |
| Phase 3 synthesis | One master synthesis agent at `2026-06-22T03:59:45Z` | `FINAL-SPEC.md`. |
| Phase 4 guide | Coordinator summary | `original-README.md` and final artifact list. |

## File Provenance

| File | Phase | Agent/session | Prompt part | Created from | Historical role |
| --- | --- | --- | --- | --- | --- |
| `research-cdx-api.md` | Phase 0 | `R1`, `ses_1128b9406ffenCJOWWWB34cW0f` | `prt_eed746c19001faDAF3DtOQwThL` | Initial orchestration prompt | CDX API, pagination, dedup fields, rate-limit, and `id_` fetch research. |
| `research-tooling.md` | Phase 0 | `R2`, `ses_1128b93c3ffeqDBtfaUrq5oS6u` | `prt_eed746c4f001AEdgDQ67M6CprQ` | Initial orchestration prompt | Recovery/download tooling comparison. |
| `research-hosting.md` | Phase 0 | `R3`, `ses_1128b9395ffe3ShHU9BWcqgHa1` | `prt_eed746c80001zEr089erLDGz5n` | Initial orchestration prompt | Static hosting and Tailscale/Caddy/nginx research. |
| `research-dedup.md` | Phase 0 | `R4`, `ses_1128b9362ffenZ31k6Uo2qcPwP` | `prt_eed746cad001PXmJzsq0QFM4TW` | Initial orchestration prompt | Deduplication, URL normalization, artifact cleanup, and file tree strategy. |
| `research-orchestration.md` | Phase 0 | `R5`, `ses_1128b9324ffeAN7HHSuqtrs2ag` | `prt_eed746ce9001lmO4cV4Wf7OkvE` | Initial orchestration prompt | Async orchestration, SQLite WAL, backoff, logging, Docker/venv tradeoffs. |
| `spec-minimalist.md` | Phase 1 | `S1`, `ses_1128905d2ffeNLuOzPvUwP5Qcy` | `prt_eed76fa42001sdRPdi5kkSkE7E` | All five research docs | Minimalist waybackpack/bash/SQLite/nginx/Tailscale design. |
| `spec-pythonic-async.md` | Phase 1 | `S2`, `ses_1128905a0ffe57LF2G1VJZSPOB` | `prt_eed76fa71001zFOavxIbUZwVwt` | All five research docs | Python async/httpx/SQLite WAL/Caddy design; later selected as the primary basis. |
| `spec-containerized.md` | Phase 1 | `S3`, `ses_112890577ffeegbrdnw8xBBwdQ` | `prt_eed76faa2001vIqvkqNfpbvt7J` | All five research docs | Docker Compose service design. |
| `review-reliability.md` | Phase 2 | `T1`, `ses_112858b90ffeNigN7VGIBLRZz0` | `prt_eed7a74810015ePFoe5RqgoAGZ` | Five research docs and three specs | Reliability and correctness tournament review. |
| `review-dx.md` | Phase 2 | `T2`, `ses_112858b68ffeU3NCkFeWmD3Mjr` | `prt_eed7a74a6001eQxNqHbRIkH7mN` | Five research docs and three specs | Developer experience and maintainability tournament review. |
| `review-production.md` | Phase 2 | `T3`, `ses_112858b43fferSUQcVCSSwMMMg` | `prt_eed7a74cb001E5a5gsiq5FrdNA` | Five research docs and three specs | Production readiness tournament review. |
| `FINAL-SPEC.md` | Phase 3 | Master synthesis, `ses_112840763ffeIuycrn3bjSIVkF` | `prt_eed7bf8ae001UHtj3qoXwfitQh` | Research docs, specs, and reviews | Final authoritative build document. |
| `original-README.md` | Phase 4 | Coordinator | `prt_eed7fc7c1001qeDWm0slyOCC6W` | Completed artifact set | Original repository guide and reading order. |
| `PROGRESS.md` | Recovery execution | Operator/coordinator, multiple later commits | Not part of initial planning session | Actual run output and post-run updates | Historical execution log for the first completed recovery. |

## Original Prompts

### Phase 0 Research Agents

The parent prompt launched the research phase with this instruction:

```text
PHASE 0 — PARALLEL RESEARCH (5 subagents, all simultaneous)

Spawn R1 through R5 at the same time. Do not wait for one before starting the next.
```

`research-cdx-api.md` was created from this prompt:

```text
You are R1 in Phase 0. Research the Internet Archive Wayback CDX Server API for recovering kyledurepos.com from a blank Linux folder. Cover query params: url, output, fl, collapse, filter, from, to, limit, matchType, resumeKey; explain collapse=digest vs collapse=urlkey; explain the id_ modifier purpose and why ALL content fetch URLs must use web.archive.org/web/{ts}id_/{url}; rate limits including CDX ~60 req/min and memento ~30 req/sec; pagination via resumeKey; best field selection for dedup/download. Write a complete markdown artifact to /home/mojo/projects/archivebackup/research-cdx-api.md. Include concrete example CDX URLs for kyledurepos.com. Do not ask questions. Return a one-paragraph status summary and confirm the file path written.
```

`research-tooling.md` was created from this prompt:

```text
You are R2 in Phase 0. Compare download tooling for Wayback recovery of kyledurepos.com: waybackpack, wget --mirror, Python wayback library (WaybackClient), internetarchive CLI, and scrapy with Wayback middleware. Evaluate each on resumability, parallel worker support, binary file handling, rate-limit compliance, id_ support/clean captures, and clean file tree output. Recommend when each is appropriate. Write a complete markdown artifact to /home/mojo/projects/archivebackup/research-tooling.md. Do not ask questions. Return a one-paragraph status summary and confirm the file path written.
```

`research-hosting.md` was created from this prompt:

```text
You are R3 in Phase 0. Research static site hosting for a flat-file Wayback mirror destined for local testing and Tailscale reverse proxy at pwned.ussyco.de. Compare nginx vs caddy for URL path rewriting, .html extension fallback, trailing slash handling, MIME types for mixed assets, directory index behavior for testing, HTTPS auto-provisioning, and Tailscale serve/funnel integration. Include concrete nginx and Caddy config patterns and tailscale commands. Write a complete markdown artifact to /home/mojo/projects/archivebackup/research-hosting.md. Do not ask questions. Return a one-paragraph status summary and confirm the file path written.
```

`research-dedup.md` was created from this prompt:

```text
You are R4 in Phase 0. Research dedup and post-processing for Wayback site recovery: combining CDX digest dedup and SHA256 on-disk dedup; stripping residual Wayback artifacts from saved HTML; URL normalization for file naming including query strings, fragments, trailing slashes, index pages; snapshot selection strategy such as most recent 200 vs highest quality/status/mimetype; file tree organization mirror path vs hash-named. Include concrete recommendations for kyledurepos.com. Write a complete markdown artifact to /home/mojo/projects/archivebackup/research-dedup.md. Do not ask questions. Return a one-paragraph status summary and confirm the file path written.
```

`research-orchestration.md` was created from this prompt:

```text
You are R5 in Phase 0. Research orchestration and automation for a Wayback recovery pipeline: Python async (asyncio + httpx with Semaphore) vs shell scripting; SQLite WAL mode for checkpoint/resume state DB; parallel worker patterns that stay within CDX/content rate limits; 429 exponential backoff implementation; structured logging per URL and summary stats; Docker vs virtualenv. Include concrete implementation recommendations for kyledurepos.com. Write a complete markdown artifact to /home/mojo/projects/archivebackup/research-orchestration.md. Do not ask questions. Return a one-paragraph status summary and confirm the file path written.
```

### Phase 1 Spec Agents

The parent prompt launched the design phase with this instruction:

```text
PHASE 1 — PARALLEL SPEC DRAFTING (3 subagents, all simultaneous)

Each subagent reads ALL 5 research docs and writes a complete, self-contained, opinionated, buildable spec.
```

`spec-minimalist.md` was created from this prompt:

```text
You are S1 in Phase 1. Read all five Phase 0 artifacts in /home/mojo/projects/archivebackup: research-cdx-api.md, research-tooling.md, research-hosting.md, research-dedup.md, research-orchestration.md. Write a complete, self-contained, opinionated, buildable spec named /home/mojo/projects/archivebackup/spec-minimalist.md for a Minimalist Pipeline using waybackpack + bash scripts, SQLite state tracking, nginx serving, and tailscale serve HTTPS tunnel. Prioritize fewest dependencies and fastest setup, while honoring hard constraints: CDX collapse=digest plus SHA256 on-disk dedup; id_ modifier on ALL content fetch URLs; <=1 CDX API req/sec, ~60 req/min ceiling, exponential backoff on 429; static output only; serve target pwned.ussyco.de via Tailscale reverse proxy. Include: ASCII architecture diagram, file tree, all CLI commands in order, full nginx config, dedup strategy, error handling. No placeholders or stubs. Return a one-paragraph status summary and confirm the file path written.
```

`spec-pythonic-async.md` was created from this prompt:

```text
You are S2 in Phase 1. Read all five Phase 0 artifacts in /home/mojo/projects/archivebackup: research-cdx-api.md, research-tooling.md, research-hosting.md, research-dedup.md, research-orchestration.md. Write a complete, self-contained, opinionated, buildable spec named /home/mojo/projects/archivebackup/spec-pythonic-async.md for a Pythonic Async pipeline using custom httpx + asyncio, Semaphore rate limiting, custom CDX client with resumeKey pagination, SQLite WAL state DB, Caddy auto-HTTPS/static serving, and tailscale serve or funnel. Honor hard constraints: CDX collapse=digest plus SHA256 on-disk dedup; id_ modifier on ALL content fetch URLs; <=1 CDX API req/sec, ~60 req/min ceiling, exponential backoff on 429; static output only; serve target pwned.ussyco.de via Tailscale reverse proxy. Include: ASCII architecture diagram, module breakdown, async worker design, SQLite schema DDL, full Caddyfile, dedup logic pseudocode. No placeholders or stubs. Return a one-paragraph status summary and confirm the file path written.
```

`spec-containerized.md` was created from this prompt:

```text
You are S3 in Phase 1. Read all five Phase 0 artifacts in /home/mojo/projects/archivebackup: research-cdx-api.md, research-tooling.md, research-hosting.md, research-dedup.md, research-orchestration.md. Write a complete, self-contained, opinionated, buildable spec named /home/mojo/projects/archivebackup/spec-containerized.md for a Containerized pipeline using docker-compose services: cdx-crawler, downloader, deduplicator, webserver; nginx container with try_files rewrites; Tailscale sidecar; Makefile lifecycle. Honor hard constraints: CDX collapse=digest plus SHA256 on-disk dedup; id_ modifier on ALL content fetch URLs; <=1 CDX API req/sec, ~60 req/min ceiling, exponential backoff on 429; static output only; serve target pwned.ussyco.de via Tailscale reverse proxy. Include: ASCII architecture diagram, full docker-compose.yml, full nginx.conf, Makefile targets, volume strategy, Tailscale sidecar config. No placeholders or stubs. Return a one-paragraph status summary and confirm the file path written.
```

### Phase 2 Review Agents

The parent prompt launched the review phase with this instruction:

```text
PHASE 2 — REVIEW TOURNAMENT (3 subagents, all simultaneous)

Each reviewer reads all 3 specs + all 5 research docs. Score each spec 1–10 per criterion. No spec is given preference.
```

`review-reliability.md` was created from this prompt:

```text
You are T1 in Phase 2. Read all five research docs and all three specs in /home/mojo/projects/archivebackup: research-cdx-api.md, research-tooling.md, research-hosting.md, research-dedup.md, research-orchestration.md, spec-minimalist.md, spec-pythonic-async.md, spec-containerized.md. Perform a Reliability & Correctness tournament review. Evaluate all three specs neutrally on: rate limit handling + 429 backoff, dedup correctness (false dedups vs missed duplicates), resumability on interruption, correct id_ usage and artifact avoidance, binary file handling. Score each spec 1-10 per criterion. List top strengths and critical gaps per spec. Write /home/mojo/projects/archivebackup/review-reliability.md. Return a one-paragraph status summary and confirm the file path written.
```

`review-dx.md` was created from this prompt:

```text
You are T2 in Phase 2. Read all five research docs and all three specs in /home/mojo/projects/archivebackup: research-cdx-api.md, research-tooling.md, research-hosting.md, research-dedup.md, research-orchestration.md, spec-minimalist.md, spec-pythonic-async.md, spec-containerized.md. Perform a Developer Experience & Maintainability tournament review. Evaluate all three specs neutrally on: debuggability when things go wrong, progress visibility during long runs, extensibility for new pipeline steps, cleanliness of output file tree, time-to-first-run from a blank folder. Score each spec 1-10 per criterion. List top strengths and critical gaps per spec. Write /home/mojo/projects/archivebackup/review-dx.md. Return a one-paragraph status summary and confirm the file path written.
```

`review-production.md` was created from this prompt:

```text
You are T3 in Phase 2. Read all five research docs and all three specs in /home/mojo/projects/archivebackup: research-cdx-api.md, research-tooling.md, research-hosting.md, research-dedup.md, research-dedup.md, research-orchestration.md, spec-minimalist.md, spec-pythonic-async.md, spec-containerized.md. Perform a Production Readiness tournament review. Evaluate all three specs neutrally on: robustness of serve config for public traffic, HTTPS + MIME types + cache headers, security posture (no directory listing, no open redirects), Tailscale integration quality, ease of incremental updates when new snapshots exist. Score each spec 1-10 per criterion. List top strengths and critical gaps per spec. Write /home/mojo/projects/archivebackup/review-production.md. Return a one-paragraph status summary and confirm the file path written.
```

### Phase 3 Synthesis Agent

`FINAL-SPEC.md` was created from this prompt:

```text
You are the Phase 3 master synthesis subagent. Read all artifacts in /home/mojo/projects/archivebackup: research-cdx-api.md, research-tooling.md, research-hosting.md, research-dedup.md, research-orchestration.md, spec-minimalist.md, spec-pythonic-async.md, spec-containerized.md, review-reliability.md, review-dx.md, review-production.md. Tally the review scores. Cherry-pick the strongest component from each spec per domain. Resolve conflicts using research evidence. Assemble /home/mojo/projects/archivebackup/FINAL-SPEC.md as the single authoritative build document for recovering kyledurepos.com from Wayback and serving it locally/Tailscale at pwned.ussyco.de.

FINAL-SPEC.md must contain these exact complete sections with no placeholders and complete configs:
1. Executive Summary - what this builds and why these choices
2. Architecture Overview - ASCII pipeline diagram end to end
3. Component Decision Log - which spec each component came from and why
4. Phase 1: CDX Discovery - full query strategy, pagination, field selection, output schema
5. Phase 2: Download Pipeline - tool, async worker count, rate limiting, id_ usage, file naming, binary handling
6. Phase 3: Deduplication - SHA256 pass, URL normalization, snapshot selection logic
7. Phase 4: Post-Processing - artifact stripping, link rewriting for local serve, MIME audit
8. Phase 5: Local Serve Setup - complete server config (not pseudocode), directory structure
9. Phase 6: Tailscale + pwned.ussyco.de - complete tunnel + DNS config
10. State DB Schema - SQLite DDL for all tables
11. CLI Reference - every command in order, from blank folder to live site
12. Error Handling Matrix - every relevant HTTP status code and how it's handled
13. Estimated Timeline - per-phase time estimates for a typical small personal site archive
14. Open Questions - decisions that require user input before build starts

Hard constraints to preserve: Dual-layer dedup CDX collapse=digest plus SHA256 on-disk; id_ modifier on ALL fetch URLs; <=1 CDX API req/sec with ~60 req/min ceiling and exponential backoff on 429; static output only; serve target pwned.ussyco.de via Tailscale reverse proxy. Ensure all config snippets are complete and actionable, no '# add config here' stubs. Return a one-paragraph status summary and confirm the file path written.
```

## Progress Log Provenance

`PROGRESS.md` was not part of the initial circular tournament planning session. It was created later during the actual recovery run and updated across multiple commits as stages completed.

| Commit | Time | Message | Historical role |
| --- | --- | --- | --- |
| `fe94d0d` | `2026-06-22T19:58:56Z` | `Document recovery init and inventory` | Created the progress log and recorded init plus CDX inventory. |
| `641b30a` | `2026-06-22T20:04:26Z` | `Document recovery selection` | Recorded capture selection. |
| `0415d12` | `2026-06-22T20:25:14Z` | `Document recovery downloads` | Recorded download results. |
| `c508505` | `2026-06-22T21:17:27Z` | `Document recovery normalization feedback` | Recorded dependency and normalization state. |
| `9ad528e` | `2026-06-22T21:33:39Z` | `Document recovery model and privacy` | Recorded content model and privacy review. |
| `580d7fe` | `2026-06-22T23:06:03Z` | `Document passed recovery validation` | Recorded validation passing with waivers. |
| `6c3be24` | `2026-06-22T23:14:18Z` | `Document recovery promotion` | Recorded promotion and local serve validation. |
| `a88f40a` | `2026-06-25T21:59:57Z` | `Document forum publication updates` | Recorded later forum/publication/media updates. |
