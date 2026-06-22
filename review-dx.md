# Developer Experience & Maintainability Tournament Review

Phase 2 role: T2  
Scope: `spec-minimalist.md`, `spec-pythonic-async.md`, and `spec-containerized.md`, evaluated against the Phase 0 research documents for CDX usage, tooling, hosting, deduplication, and orchestration.

## Executive Ranking

1. **Pythonic Async**: Best overall DX and maintainability balance. It has the clearest failure model, structured logs, typed module boundaries, durable SQLite state, and a clean static output tree without making first-run setup too heavy.
2. **Containerized**: Strongest reproducibility and operational isolation, but slower to first successful run and more complex to debug because failures can span Compose services, bind mounts, container users, Tailscale sidecar state, and generated artifacts.
3. **Minimalist**: Fastest to understand and closest to shell-level observability, but the bash/SQLite implementation becomes brittle as soon as recovery needs richer validation, HTML cleanup, alternate capture selection, or new pipeline steps.

## Score Matrix

Scores are 1-10, where 10 is strongest for the criterion.

| Spec | Debuggability When Things Go Wrong | Progress Visibility During Long Runs | Extensibility For New Pipeline Steps | Cleanliness Of Output File Tree | Time-To-First-Run From Blank Folder | Total |
|---|---:|---:|---:|---:|---:|---:|
| Minimalist | 6 | 5 | 4 | 7 | 8 | 30 |
| Pythonic Async | 9 | 9 | 9 | 9 | 7 | 43 |
| Containerized | 7 | 8 | 8 | 8 | 5 | 36 |

## Criterion Notes

**Debuggability When Things Go Wrong**

Pythonic Async wins. It specifies JSONL events, durable retry events, explicit job state, stale `in_progress` recovery, module-level ownership, and a report with failed URLs and last errors. Containerized has similar state and logs, but Compose adds extra failure domains: service dependencies, image build failures, volume permissions, sidecar networking, and container health checks. Minimalist is transparent because it uses shell, `curl`, logs, and SQLite directly, but bash quoting, embedded Python snippets, mutable `.part` files, and limited validation make subtle errors harder to isolate.

**Progress Visibility During Long Runs**

Pythonic Async again leads because it requires structured event names for CDX pages, enqueueing, fetch starts, retries, successes, duplicate skips, collision resolution, and report output. Containerized provides JSONL logs and service-level status, plus `make logs`, but progress is split across services and requires Compose awareness. Minimalist has `logs/cdx.log`, `logs/fetch.log`, and SQL summaries, but the logs are plain text and do not provide the same machine-readable lifecycle visibility or per-stage metrics during long runs.

**Extensibility For New Pipeline Steps**

Pythonic Async is the most maintainable platform for adding asset expansion, alternate capture selection, validation passes, richer reports, or hosting changes. Its module breakdown maps cleanly to CDX, DB, fetch, dedup, HTML, paths, rate limiting, and reporting. Containerized is also extensible because stages are separated, but adding a new step often means changing the Python CLI, image contract, Compose graph, volumes, Makefile, and service dependencies. Minimalist can add scripts, but cross-script state contracts, shell escaping, repeated SQLite fragments, and embedded Python snippets will degrade quickly.

**Cleanliness Of Output File Tree**

Pythonic Async is strongest. It puts the public site under `recovered/kyledurepos.com/site/`, keeps manifests beside it, avoids symlink output, defines deterministic URL mapping, records aliases, and performs conservative parser-based HTML cleanup. Containerized is also clean and explicitly keeps `data`, `logs`, `raw`, `reports`, and manifests private while serving only the site subtree, though hardlinking duplicates for navigability can make the tree less conceptually simple. Minimalist produces a clear static site tree and keeps SQLite out of runtime serving, but its HTML cleanup is absent from the actual shell pipeline, so Wayback artifacts and unrepaired links are more likely to leak into the served tree.

**Time-To-First-Run From A Blank Folder**

Minimalist wins. It gives copyable Ubuntu/Debian commands and sequential scripts that can run without implementing a full package or container image first. Pythonic Async is reasonable but assumes an implementation behind the CLI and Python 3.12 packaging before the documented commands work. Containerized is slowest to first run because it needs Docker, Compose, image build, config files, bind mounts, service ordering, and optional Tailscale auth before the full path is operational.

## Spec: Minimalist

### Top Strengths

- Lowest setup burden and easiest mental model from a blank Linux folder.
- Uses familiar tools: bash, `curl`, `sqlite3`, nginx, and Tailscale.
- Honors core hard requirements: `collapse=digest`, `id_` content URLs, serialized CDX, retry/backoff, SQLite state, SHA256 dedup, and static output.
- Direct shell scripts make it easy to run one stage at a time and inspect generated files manually.
- nginx config is explicit and follows the research recommendation to avoid catch-all SPA fallback.

### Critical Gaps

- Bash is a weak long-term orchestration layer for nuanced retry behavior, content validation, alternate capture selection, and structured event logging.
- HTML cleanup and link rewriting are not implemented in the pipeline, so recovered pages may retain Wayback artifacts or broken archive-wrapped URLs despite the research recommending parser-based cleanup.
- Progress logs are text logs rather than structured JSONL, which makes long-run monitoring and postmortems weaker.
- `UNIQUE(cdx_digest)` in `captures` can discard useful URL aliases too early; the research recommends preserving URL-to-digest mappings even when skipping duplicate downloads.
- The fetch loop is effectively single-job sequential, so long recoveries may be much slower than necessary even with polite content concurrency.
- Extending the pipeline likely means more shell plus embedded Python, increasing quoting, transaction, and error-handling risk.

## Spec: Pythonic Async

### Top Strengths

- Best alignment with orchestration research: `asyncio`, `httpx.AsyncClient`, SQLite WAL, bounded concurrency, durable retry state, JSONL logs, and clear reports.
- Strong failure diagnosis through explicit DB tables, job statuses, retry events, structured logs, and stale job recovery.
- Clean module boundaries make future work maintainable: CDX, DB, fetch, rate limiting, paths, dedup, HTML cleanup, logging, reporting, and config are separated without fragmenting into independent services.
- Output layout is clean and operationally safe: static site under `recovered/kyledurepos.com/site/`, manifests and reports outside the served tree, no dynamic runtime dependency.
- Strong path mapping, duplicate aliasing, final SHA256 dedup, and conservative HTML cleanup match the dedup and hosting research well.
- Reasonable first-run flow once implemented: virtualenv, editable install, config, then `archive-recovery run`.

### Critical Gaps

- Requires real implementation work before any command can run; the spec is more maintainable but not as immediately executable as the shell design.
- Python 3.12 requirement may slow setup on systems where only older distro Python versions are installed.
- The schema and module plan are comprehensive, but implementation discipline is required to avoid overengineering before the first successful recovery.
- Asset discovery expansion is implied by modules and HTML/CSS parsing but not as operationally staged as the core discover/enqueue/fetch flow.
- The spec should explicitly define how `manifest.jsonl` is emitted because acceptance criteria require it, while the schema primarily records state in SQLite.

## Spec: Containerized

### Top Strengths

- Most reproducible runtime environment once built: pinned Python base image, Docker Compose services, bind-mounted durable state, nginx container, and Tailscale sidecar.
- Clear stage separation between CDX crawling, downloading, deduplication, static serving, and exposure.
- Good operational controls through Makefile targets, health checks, `docker compose ps`, `make logs`, and validation commands.
- Keeps public serving clean: nginx serves only `recovered/kyledurepos.com/site/`; raw blobs, SQLite, logs, reports, and Tailscale state stay outside the web root.
- Strong raw-object preservation through `raw/sha256/`, which helps auditability and reprocessing.
- Compose model is a good fit if the pipeline must be handed off, rerun on another host, or kept running with stable service boundaries.

### Critical Gaps

- Highest time-to-first-run cost: Docker/Compose setup, image build, config files, directory initialization, service sequencing, and Tailscale auth all need to be correct.
- Debugging crosses multiple layers: Python code, container image, Compose networking, bind mount ownership, nginx health, and Tailscale sidecar state.
- File ownership can become painful because the pipeline image runs as UID `1000:1000` while host directories may not match.
- The Tailscale service definition is risky: `TS_SERVE_CONFIG` is provided, but the command starts `tailscaled`; operational steps still execute `tailscale up` and `tailscale serve` manually, so automation is not fully self-contained.
- `make clean` removes `data`, `logs`, `raw`, `recovered`, and `reports`; useful, but hazardous for DX unless guarded or clearly separated from routine cleanup.
- Adding a new pipeline step requires edits in several places: Python CLI, Dockerfile contract if dependencies change, Compose service graph, Makefile, volumes, and docs.

## Tournament Verdict

For developer experience and maintainability, **Pythonic Async** is the best Phase 2 winner. It preserves the research-backed recovery requirements while giving operators the best tools to understand failures, watch progress, resume safely, add future pipeline stages, and keep the public file tree clean. **Containerized** is the best deployment and handoff model after the Python CLI stabilizes, but it is not the best first implementation path. **Minimalist** is valuable as a bootstrap or smoke-test approach, but it should not be the long-term recovery pipeline if correctness, auditability, and maintainability matter.
