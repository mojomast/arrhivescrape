# Reliability & Correctness Tournament Review

Reviewer: T1, Phase 2

Scope: Neutral review of `spec-minimalist.md`, `spec-pythonic-async.md`, and `spec-containerized.md` against the Phase 0 research documents for Wayback recovery of `kyledurepos.com`.

## Evaluation Criteria

Scores are 1-10, where 10 means the spec is explicit, internally consistent, and low-risk for the criterion.

| Spec | Rate limits + 429 backoff | Dedup correctness | Resumability | Correct `id_` usage + artifact avoidance | Binary file handling | Average |
|---|---:|---:|---:|---:|---:|---:|
| Minimalist | 7 | 6 | 7 | 8 | 7 | 7.0 |
| Pythonic Async | 9 | 8 | 9 | 9 | 9 | 8.8 |
| Containerized | 8 | 8 | 7 | 9 | 8 | 8.0 |

## Tournament Result

1. `spec-pythonic-async.md` wins on reliability and correctness. It has the most complete model for durable retries, `Retry-After`, CDX pagination state, stale job recovery, byte-preserving downloads, artifact cleanup, and SHA256-based output correctness.
2. `spec-containerized.md` is second. It is strong on architecture, rate-limit policy, raw-byte storage, and static serving isolation, but its staged service model leaves more restart and cross-stage consistency risk than the Pythonic async spec.
3. `spec-minimalist.md` is third. It is pragmatic and auditable, but shell-based JSON parsing, URL encoding, retry handling, stale in-progress recovery, and dedup alias preservation are weaker than the Python designs.

## Spec: Minimalist

### Scores

| Criterion | Score | Rationale |
|---|---:|---|
| Rate limits + 429 backoff | 7 | CDX is serialized with `sleep 1`, retryable statuses are listed, and content retry state is persisted. However, neither CDX nor content retries honor `Retry-After`, there is no jitter, and content fetch is single-job sequential rather than adaptively throttled. |
| Dedup correctness | 6 | It uses `collapse=digest`, `UNIQUE(cdx_digest)`, and post-download SHA256, which prevents many duplicate downloads. The critical weakness is that `UNIQUE(cdx_digest)` and CDX collapse can discard useful URL/timestamp aliases before they are recorded, increasing missed URL mappings and risking false loss of semantically important paths. |
| Resumability | 7 | Discovery, enqueue, and fetch are mostly idempotent, and `retry_wait` is persisted. Missing stale `in_progress` recovery means interruption during a fetch can strand a job permanently unless manually reset. CDX resume progress is page-file based rather than durably tracked as a query cursor in SQLite. |
| Correct `id_` usage + artifact avoidance | 8 | The authoritative fetcher stores `archive_url` with `id_` and uses it consistently. Artifact avoidance relies mostly on `id_`; the spec does not implement parser-based HTML cleanup or link rewriting, so residual Wayback artifacts and archive-wrapped links may remain. |
| Binary file handling | 7 | `curl -o` and SHA256 over files preserve bytes, and nginx serves assets with MIME types. There is no response MIME/body validation, no magic-byte validation, and path inference can still treat unknown or extensionless binary content as HTML when MIME is absent. |

### Top Strengths

- Simple, auditable scripts with few moving parts.
- Enforces `id_` in the authoritative fetch path.
- Uses SQLite WAL and persisted job state rather than pure files.
- Writes to `.part` files and moves only after non-empty `200` responses and SHA256 calculation.
- Static nginx hosting has correct exact-file-first behavior and returns `404` for missing files.

### Critical Gaps

- Does not honor `Retry-After` on `429`, despite research recommending it.
- No stale `in_progress` recovery after interruption during content fetch.
- `UNIQUE(cdx_digest)` can erase aliases before manifesting them, producing missed duplicate mappings and potentially losing navigable URL paths.
- No parser-based HTML cleanup or archive URL rewriting, so `id_` is doing too much of the artifact-avoidance work alone.
- No binary validation beyond non-empty body and SHA256.

## Spec: Pythonic Async

### Scores

| Criterion | Score | Rationale |
|---|---:|---|
| Rate limits + 429 backoff | 9 | CDX has concurrency `1`, minimum request interval, `resumeKey` pagination, capped exponential backoff with jitter, and `Retry-After` parsing. Content retries are durably scheduled in SQLite. Minor risk remains around implementing per-host concurrency and adaptive throttling correctly. |
| Dedup correctness | 8 | It combines CDX `collapse=digest`, local selection, raw/final SHA256, output aliases, collision checks, and manifest records. The main risk is that the primary collapsed CDX pass may miss alternate URL/timestamp records unless supplemental discovery or alias capture is implemented beyond what CDX returns. |
| Resumability | 9 | SQLite WAL, `cdx_queries`, persisted resume keys, stale `in_progress` recovery, idempotent commands, due-job claiming, and durable retry events provide the strongest interruption model. Correctness depends on careful implementation of atomic file moves and short DB transactions, which the spec calls out. |
| Correct `id_` usage + artifact avoidance | 9 | It forbids plain replay fetches, constructs all content URLs with `id_`, and specifies conservative parser-based cleanup of known Wayback artifacts and archive-wrapped internal URLs. The only residual risk is that `id_` HTML plus cleanup may still miss some referenced assets unless parsing/enqueue expansion is implemented thoroughly. |
| Binary file handling | 9 | It explicitly requires streaming binary responses as bytes, never decoding non-text assets, preserving asset extensions, computing raw/final hashes, and serving MIME types through Caddy. It also separates HTML cleanup from binary paths. |

### Top Strengths

- Best end-to-end reliability design: SQLite WAL state, idempotent commands, durable retries, and stale-job recovery.
- Strongest `429` handling, including `Retry-After`, jitter, capped backoff, and no in-memory-only retry loop.
- Strong artifact controls: `id_` only plus conservative parser-based cleanup and internal archive URL rewriting.
- Strong binary handling requirements, including byte streaming and no accidental text decoding.
- Rich manifest/log/report model supports auditing correctness after recovery.

### Critical Gaps

- Still relies on `collapse=digest` for the primary CDX pass, which can hide alternate URL/timestamp rows needed for complete alias mapping.
- Dedup pseudocode says skipped duplicate CDX digests are recorded, but if the CDX query has already collapsed them, those skipped rows may never be seen.
- More implementation surface area means correctness depends on disciplined engineering of async DB access, atomic writes, and queue claiming.
- Asset expansion is described, but acceptance criteria focus more on initial CDX and fetch than proving discovered HTML/CSS references are resolved through alternate captures.

## Spec: Containerized

### Scores

| Criterion | Score | Rationale |
|---|---:|---|
| Rate limits + 429 backoff | 8 | CDX concurrency, interval, `Retry-After`, jittered exponential backoff, and max attempts are explicit. Content retry persistence is specified. It is slightly weaker than Pythonic Async because the Compose stage boundaries and separate services make global backpressure and retry orchestration less clearly defined. |
| Dedup correctness | 8 | The raw content-addressed store, final SHA256, manifests, duplicates, and optional hardlinks for navigability are strong. Risks remain around CDX `collapse=digest` hiding aliases, and around the deduplicator needing to reconcile raw objects, final output paths, hardlinks, and manifests consistently after restarts. |
| Resumability | 7 | Bind-mounted SQLite, raw files, logs, and Tailscale state are durable, and rerunning `make discover`, `make download`, and `make dedupe` is supported. However, the spec has less detail on stale `in_progress` job recovery, partial raw-file cleanup, idempotent deduplicator reruns, and cross-stage consistency than Pythonic Async. |
| Correct `id_` usage + artifact avoidance | 9 | It clearly forbids plain replay URLs, mandates exact `id_` construction, validates logs for missing `id_`, and specifies parser-based cleanup of known Wayback artifacts and internal archive URL rewriting. |
| Binary file handling | 8 | Streaming to a raw SHA256 store and later deduplicating into static output is robust for binary bytes. It calls for MIME/body validation and asset extension preservation. Slight risk remains from the split downloader/deduplicator flow and optional hardlinks, which must be carefully handled for portability and static-site navigability. |

### Top Strengths

- Strong operational isolation: public nginx serves only `recovered/kyledurepos.com/site`, not raw files, manifests, logs, or SQLite.
- Strong `id_` guarantees and validation requirement that logs contain no non-`id_` archive downloads.
- Raw content-addressed storage is the best design for auditability and binary preservation.
- Rate-limit defaults are conservative and explicit for CDX and content fetches.
- Docker volumes make state durable across container recreation.

### Critical Gaps

- Stale `in_progress` recovery and idempotent deduplicator restart semantics are not specified as rigorously as in Pythonic Async.
- `collapse=digest` plus skipping duplicate digest jobs can miss aliases unless uncollapsed supplemental inventory or alias-preserving CDX discovery exists.
- Compose `depends_on: service_completed_successfully` creates a simple batch pipeline, but long-running retry waits or partial failures may need more nuanced orchestration than the spec describes.
- Tailscale sidecar setup is operationally more complex and could distract from recovery correctness if auth/state handling fails.
- Optional hardlinks for duplicate navigability are useful but add correctness complexity compared with manifest-only aliases.

## Cross-Spec Findings

### Rate Limit Handling + 429 Backoff

`spec-pythonic-async.md` is strongest because it models retries as durable scheduled state and honors `Retry-After` for both CDX and content. `spec-containerized.md` is also strong, but orchestration boundaries make global retry behavior less concrete. `spec-minimalist.md` has acceptable capped exponential backoff but misses `Retry-After` and jitter.

### Dedup Correctness

All three specs meet the stated hard requirement to use `collapse=digest` and SHA256 after download. The shared correctness risk is over-reliance on collapsed CDX discovery. Research says `collapse=digest` can hide useful timestamp and URL variants, so the safest implementation should either run an uncollapsed inventory pass for aliases or otherwise record alias relationships from a broader CDX result set before pruning downloads.

### Resumability

`spec-pythonic-async.md` has the most complete interruption model, including stale `in_progress` recovery and persisted CDX cursor state. `spec-containerized.md` has durable volumes but needs clearer job-state recovery details. `spec-minimalist.md` is rerunnable for normal cases but can strand jobs interrupted after they are marked `in_progress`.

### Correct `id_` Usage And Artifact Avoidance

All three specs correctly prefer `id_` for automated content fetches. Pythonic Async and Containerized are stronger because they also specify parser-based cleanup and archive URL rewriting. Minimalist correctly uses `id_`, but lacks the post-processing layer recommended by the research docs.

### Binary File Handling

Pythonic Async is strongest because it explicitly prohibits decoding non-text assets and requires byte streaming. Containerized is close due to raw SHA256 blob storage. Minimalist preserves bytes via `curl`, but validation and MIME-aware handling are comparatively thin.

## Recommended Reliability Fixes Before Implementation

1. Add an alias-preserving CDX inventory strategy to whichever spec wins: use `collapse=digest` for required primary discovery, but add an uncollapsed or targeted supplemental pass to preserve URL/timestamp aliases before download pruning.
2. Require `Retry-After` handling everywhere `429` is retried, including Minimalist CDX and content fetches.
3. Require stale `in_progress` recovery in Minimalist and Containerized.
4. Require parser-based HTML cleanup and archive URL rewriting in Minimalist if it remains a candidate.
5. Add explicit binary validation checks for all specs: magic bytes for common images/fonts/PDFs, reject HTML error bodies for expected CSS/JS/binary assets, and record response `Content-Type` separately from CDX MIME.
