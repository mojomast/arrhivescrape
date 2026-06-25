# Research: Orchestration and Automation for Wayback Recovery

Target site: `kyledurepos.com`

Phase: 0 research

Role: R5

Date: 2026-06-22

## Executive Recommendation

Use a Python-based asynchronous recovery pipeline built on `asyncio`, `httpx.AsyncClient`, bounded concurrency with `asyncio.Semaphore`, SQLite in WAL mode for durable checkpoint/resume state, and structured JSON logging. Prefer a local Python virtual environment for development and early recovery runs, with an optional Docker image once the pipeline is stable and repeatable.

For `kyledurepos.com`, the pipeline should be conservative by default: separate rate limits for CDX discovery and archived content fetches, exponential backoff for `429`, `503`, transient network failures, and per-URL retry state persisted in SQLite. The most reliable design is a resumable queue-driven worker model rather than shell scripts or one-shot crawls.

## Goals

- Discover archived URLs and captures for `kyledurepos.com` from the Internet Archive CDX API.
- Select the best captures for recovery, prioritizing successful HTML, CSS, JS, image, document, and media assets.
- Fetch archived content without overwhelming CDX or Wayback content endpoints.
- Persist enough state to resume after interruption without duplicating work.
- Produce auditable logs and summary statistics for recovery coverage.
- Keep implementation simple enough for local operation but robust enough for long-running jobs.

## Python Async vs Shell Scripting

### Python Async Recommendation

Use Python async as the primary orchestration layer.

Recommended stack:

- `asyncio` for worker orchestration.
- `httpx.AsyncClient` for HTTP requests.
- `asyncio.Semaphore` for concurrency limits.
- `sqlite3` or `aiosqlite` for persisted state.
- `structlog` or standard `logging` with JSON formatting for structured logs.
- `tenacity` only if retry logic remains simple and transparent; otherwise implement explicit retry loops.

Python async is the better fit because Wayback recovery is dominated by network I/O, retry behavior, checkpointing, response classification, and content normalization. These tasks are awkward and fragile in shell scripts once resume logic, per-URL status, rate limiting, and structured output are required.

### Shell Scripting Assessment

Shell scripts are useful for small support tasks:

- Running a single CDX query manually.
- Inspecting output files.
- Launching a pipeline command.
- Packaging or smoke-testing recovered output.

Shell scripts should not be the main orchestration mechanism for `kyledurepos.com` recovery because they become brittle for:

- Per-URL checkpoint state.
- Retrying individual failed captures.
- Distinguishing `429`, `404`, `503`, timeout, and content validation failures.
- Maintaining separate rate limits for CDX and content fetches.
- Emitting structured logs and summary metrics.
- Handling graceful shutdown and resume.

### Decision

Implement the recovery pipeline in Python async. Use shell only as a thin wrapper, for example `scripts/recover-kyledurepos.sh`, after the Python command interface exists.

## Proposed Pipeline Architecture

The pipeline should be split into explicit stages with durable state between them.

### Stage 1: CDX Discovery

Query CDX for `kyledurepos.com` and likely host variants:

- `kyledurepos.com/*`
- `www.kyledurepos.com/*`
- `http://kyledurepos.com/*`
- `https://kyledurepos.com/*`
- `http://www.kyledurepos.com/*`
- `https://www.kyledurepos.com/*`

Recommended CDX parameters:

```text
output=json
fl=timestamp,original,statuscode,mimetype,digest,length
filter=statuscode:200
collapse=digest
```

Use `collapse=digest` for initial deduplication, but keep enough records to revisit alternate captures if the selected capture fails content validation.

Recommended CDX behavior:

- Fetch CDX pages sequentially or with very low concurrency.
- Persist every discovered capture before content fetching starts.
- Store the raw CDX fields to avoid re-querying unnecessarily.
- Keep discovery idempotent with unique constraints on `(timestamp, original)` or `(digest, original, timestamp)`.

### Stage 2: Capture Selection

For each original URL, select one or more candidate captures.

Selection priority:

1. `statuscode = 200`.
2. Preferred MIME type for the URL extension.
3. Most recent capture if recovering latest known site state.
4. Oldest stable capture if reconstructing an earlier historical version.
5. Alternate digest if the first selected capture fetches a Wayback error page or redirect trap.

For `kyledurepos.com`, default to latest successful captures unless project evidence suggests a specific historical date is required.

### Stage 3: Content Fetch

Fetch archived content from URLs of this form:

```text
https://web.archive.org/web/{timestamp}id_/{original_url}
```

Use `id_` mode for raw-ish content where appropriate, especially assets. For HTML, fetch both normal replay and `id_` only if needed. Normal replay can help preserve rewritten resource references, while `id_` can help recover original source content.

Recommended default:

- HTML: first fetch normal replay, then parse and normalize links.
- CSS, JS, images, fonts, PDFs, media: fetch `id_`.

### Stage 4: Asset Extraction and Expansion

Parse recovered HTML and CSS to discover referenced assets not present in the initial CDX result set.

Sources to parse:

- HTML `href`, `src`, `srcset`, `poster`, inline style URLs.
- CSS `url(...)` and `@import`.
- JavaScript only if obvious static references are recoverable; avoid complex JS execution in Phase 0.

Normalize discovered URLs against the original page URL, enqueue them into the same SQLite-backed work queue, and resolve captures through CDX lookup.

### Stage 5: Output Reconstruction

Write recovered files to a deterministic local tree.

Recommended output root:

```text
recovered/kyledurepos.com/
```

Path mapping guidance:

- `/` maps to `index.html`.
- Directory URLs map to `path/index.html`.
- File URLs preserve the basename and extension.
- Query strings should be hashed or encoded into stable suffixes when materially different.
- Avoid overwriting different captures unless digest and content are identical.

## SQLite WAL Checkpoint and Resume Database

Use SQLite as the state database. Enable WAL mode at initialization.

Recommended pragmas:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;
```

WAL mode is recommended because it improves resilience and permits concurrent readers while a writer is active. The pipeline should still use a simple write pattern, ideally one DB writer connection or short transactions, because SQLite supports one writer at a time.

### Recommended Schema

```sql
CREATE TABLE IF NOT EXISTS captures (
  id INTEGER PRIMARY KEY,
  original_url TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  statuscode INTEGER,
  mimetype TEXT,
  digest TEXT,
  length INTEGER,
  source TEXT NOT NULL DEFAULT 'cdx',
  discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(original_url, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_captures_original_url
ON captures(original_url);

CREATE INDEX IF NOT EXISTS idx_captures_digest
ON captures(digest);

CREATE TABLE IF NOT EXISTS urls (
  id INTEGER PRIMARY KEY,
  original_url TEXT NOT NULL UNIQUE,
  normalized_url TEXT NOT NULL,
  url_type TEXT,
  priority INTEGER NOT NULL DEFAULT 100,
  discovered_from TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fetch_jobs (
  id INTEGER PRIMARY KEY,
  url_id INTEGER NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
  capture_id INTEGER REFERENCES captures(id) ON DELETE SET NULL,
  job_type TEXT NOT NULL DEFAULT 'content',
  status TEXT NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  last_error TEXT,
  http_status INTEGER,
  output_path TEXT,
  content_sha256 TEXT,
  bytes_written INTEGER,
  started_at TEXT,
  finished_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(url_id, capture_id, job_type)
);

CREATE INDEX IF NOT EXISTS idx_fetch_jobs_status_next_attempt
ON fetch_jobs(status, next_attempt_at, priority);
```

The index above references `priority`, so either include `priority` on `fetch_jobs` or query priority through `urls`. A simpler practical schema is to add `priority INTEGER NOT NULL DEFAULT 100` directly to `fetch_jobs`.

Corrected index if priority remains only in `urls`:

```sql
CREATE INDEX IF NOT EXISTS idx_fetch_jobs_status_next_attempt
ON fetch_jobs(status, next_attempt_at);
```

Recommended statuses:

- `pending`
- `in_progress`
- `succeeded`
- `retry_wait`
- `failed`
- `skipped`

### Resume Behavior

At startup:

- Convert stale `in_progress` jobs back to `pending` if `started_at` is older than a configured threshold.
- Select jobs where `status = 'pending'` or `status = 'retry_wait' AND next_attempt_at <= CURRENT_TIMESTAMP`.
- Never delete completed job state during normal runs.
- Use unique constraints to make enqueue operations idempotent.

On graceful shutdown:

- Stop accepting new work.
- Allow active fetches to complete within a short timeout.
- Mark unfinished active jobs as `pending` or leave them for stale-job recovery.

## Parallel Worker Pattern

Use separate semaphores and worker pools for CDX requests and content requests.

Recommended defaults for `kyledurepos.com`:

```text
CDX concurrency: 1
CDX minimum interval: 1.0 to 2.0 seconds between requests
Content concurrency: 3 to 5
Per-host content concurrency: 3
Request timeout: 30 seconds
Max attempts per job: 5
Initial backoff: 2 seconds
Max backoff: 5 minutes
Jitter: enabled
```

The Internet Archive is a shared service. Favor predictable, polite throughput over maximum parallelism.

### Worker Model

Recommended model:

- One scheduler loop queries SQLite for due jobs.
- The scheduler places due jobs onto an `asyncio.Queue`.
- A fixed number of content workers consume jobs.
- Each worker uses a content semaphore before HTTP fetch.
- CDX lookup uses its own semaphore and interval limiter.
- Job state transitions are persisted before and after network activity.

Pseudo-code:

```python
content_sem = asyncio.Semaphore(4)
cdx_sem = asyncio.Semaphore(1)

async def content_worker(queue, client):
    while True:
        job = await queue.get()
        try:
            await mark_started(job)
            async with content_sem:
                response = await fetch_with_backoff(client, job.archive_url)
            await handle_response(job, response)
        except Exception as exc:
            await mark_retry_or_failed(job, exc)
        finally:
            queue.task_done()
```

Keep database writes short. Do not hold a database transaction open while awaiting network I/O.

## Rate Limits and Backoff

### Separate CDX and Content Limits

CDX and content replay endpoints should be treated as separate constrained resources.

CDX recommendations:

- Concurrency `1`.
- Use pagination or bounded queries.
- Sleep between requests.
- Cache query results in SQLite.

Content recommendations:

- Concurrency `3` to `5` initially.
- Reduce concurrency automatically if repeated `429` or `503` responses occur.
- Avoid retry storms by persisting `next_attempt_at`.

### 429 Exponential Backoff

Behavior for `429 Too Many Requests`:

- Respect `Retry-After` if present.
- Otherwise use exponential backoff with jitter.
- Persist the next retry time in SQLite.
- Do not immediately requeue into memory only; that loses state on interruption.

Backoff formula:

```python
delay = min(max_delay, base_delay * (2 ** (attempts - 1)))
delay = delay * random.uniform(0.5, 1.5)
```

Recommended values:

```text
base_delay: 2 seconds
max_delay: 300 seconds
max_attempts: 5
```

`Retry-After` parsing:

- If integer seconds, use that value with a reasonable cap.
- If HTTP date, compute seconds until that date.
- Add small jitter even when `Retry-After` is present to avoid synchronized retries.

Retryable statuses:

- `429`
- `500`
- `502`
- `503`
- `504`
- Network timeout
- Connection reset

Usually non-retryable statuses:

- `400`
- `401`
- `403`, unless known transient Wayback behavior is observed
- `404`, unless trying alternate captures
- `410`

### Adaptive Throttling

For `kyledurepos.com`, start with conservative limits. If the first run shows no throttling, content concurrency can be raised modestly.

Recommended adaptive behavior:

- If `429` count exceeds 3 in a 5-minute window, halve content concurrency down to a minimum of 1.
- If no `429` or `503` responses occur for 15 minutes, allow concurrency to increase by 1 up to configured maximum.
- Keep CDX concurrency fixed at 1.

This can be deferred until after a static limit implementation exists. Static conservative limits are acceptable for Phase 0 and initial recovery.

## Structured Logging

Use JSON line logs so each event is machine-readable and grep-friendly.

Recommended log file:

```text
logs/kyledurepos-recovery.jsonl
```

Each content fetch log event should include:

- `event`
- `original_url`
- `archive_url`
- `timestamp`
- `job_id`
- `attempt`
- `status`
- `http_status`
- `mimetype`
- `bytes`
- `duration_ms`
- `output_path`
- `error`
- `retry_after_seconds`
- `next_attempt_at`

Example events:

```json
{"event":"fetch_started","job_id":42,"original_url":"https://kyledurepos.com/","timestamp":"20220101000000","attempt":1}
{"event":"fetch_succeeded","job_id":42,"original_url":"https://kyledurepos.com/","http_status":200,"bytes":18422,"duration_ms":812,"output_path":"recovered/kyledurepos.com/index.html"}
{"event":"fetch_retry_scheduled","job_id":43,"original_url":"https://kyledurepos.com/style.css","http_status":429,"attempt":2,"retry_after_seconds":17,"next_attempt_at":"2026-06-22T12:05:17Z"}
```

### Summary Stats

Emit a summary at the end of each run and store it as both log events and a human-readable report.

Recommended summary path:

```text
reports/kyledurepos-summary.md
```

Summary metrics:

- Total URLs discovered.
- Total captures discovered.
- Jobs pending.
- Jobs succeeded.
- Jobs failed.
- Jobs skipped.
- Retry count by reason.
- HTTP status distribution.
- MIME type distribution.
- Bytes downloaded.
- Unique content hashes recovered.
- Duplicate captures skipped.
- Top unresolved URLs.
- Start time, end time, elapsed time.

Example SQL for summary:

```sql
SELECT status, COUNT(*) FROM fetch_jobs GROUP BY status;
SELECT http_status, COUNT(*) FROM fetch_jobs GROUP BY http_status ORDER BY COUNT(*) DESC;
SELECT mimetype, COUNT(*) FROM captures GROUP BY mimetype ORDER BY COUNT(*) DESC;
```

## Docker vs Virtualenv

### Virtualenv Recommendation for Phase 0 and Initial Recovery

Use a Python virtual environment first.

Benefits:

- Faster iteration.
- Easier local debugging.
- Simpler access to the workspace and recovered files.
- Lower operational overhead.
- Good enough for a one-site recovery pipeline.

Recommended layout:

```text
.venv/
pyproject.toml
archive_recovery/
  __init__.py
  cli.py
  cdx.py
  db.py
  fetch.py
  logging.py
  paths.py
  parse.py
data/
  kyledurepos.sqlite3
logs/
  kyledurepos-recovery.jsonl
recovered/
  kyledurepos.com/
reports/
  kyledurepos-summary.md
```

Recommended commands:

```bash
python -m venv .venv
. .venv/bin/activate
pip install httpx aiosqlite beautifulsoup4 lxml tinycss2
python -m archive_recovery.cli discover --site kyledurepos.com
python -m archive_recovery.cli fetch --site kyledurepos.com --concurrency 4
python -m archive_recovery.cli report --site kyledurepos.com
```

### Docker Recommendation

Add Docker after the pipeline stabilizes or if the recovery needs to run in CI, on another machine, or under a scheduler.

Benefits:

- Reproducible runtime.
- Easier handoff.
- Cleaner dependency isolation.
- Suitable for scheduled or remote execution.

Risks and costs:

- File ownership friction on mounted volumes.
- More ceremony during active development.
- Need to mount `data`, `logs`, `recovered`, and `reports` directories carefully.

Recommended Docker stance:

- Do not make Docker mandatory for Phase 0.
- Provide a Dockerfile once CLI commands and dependencies settle.
- Use bind mounts for durable outputs.

Example future command:

```bash
docker run --rm \
  -v "$PWD/data:/app/data" \
  -v "$PWD/logs:/app/logs" \
  -v "$PWD/recovered:/app/recovered" \
  -v "$PWD/reports:/app/reports" \
  archive-recovery \
  python -m archive_recovery.cli fetch --site kyledurepos.com --concurrency 4
```

## Concrete Implementation Recommendations for kyledurepos.com

### Default Configuration

Use a site-specific config file.

Suggested path:

```text
configs/kyledurepos.com.toml
```

Suggested contents:

```toml
[site]
domain = "kyledurepos.com"
hosts = ["kyledurepos.com", "www.kyledurepos.com"]
prefer_scheme = "https"
output_root = "recovered/kyledurepos.com"

[cdx]
concurrency = 1
min_interval_seconds = 1.5
collapse = "digest"
status_filter = 200

[fetch]
content_concurrency = 4
timeout_seconds = 30
max_attempts = 5
base_backoff_seconds = 2
max_backoff_seconds = 300
use_jitter = true

[state]
sqlite_path = "data/kyledurepos.sqlite3"
stale_in_progress_minutes = 30

[logging]
jsonl_path = "logs/kyledurepos-recovery.jsonl"
summary_path = "reports/kyledurepos-summary.md"
```

### Recommended Initial Run Order

1. Initialize SQLite schema and WAL mode.
2. Run CDX discovery for both apex and `www` hostnames.
3. Insert captures and URL records idempotently.
4. Generate fetch jobs for selected captures.
5. Fetch HTML first with content concurrency `2`.
6. Parse HTML and enqueue referenced assets.
7. Fetch assets with content concurrency `4`.
8. Generate a summary report.
9. Review failed URLs and retry with alternate captures.

### URL Priority

Recommended priority values:

```text
0: homepage
10: first-level HTML pages
20: other HTML pages
30: CSS
40: JavaScript
50: images and fonts
60: PDFs and documents
90: unknown or low-value assets
```

Prioritize HTML early because it reveals additional asset dependencies.

### Capture Validation

Do not assume HTTP `200` from Wayback means useful recovered content.

Validate responses:

- Reject obvious Wayback error pages.
- Reject empty bodies for assets expected to have content.
- Verify image magic bytes for common image extensions when possible.
- Verify CSS and JS are not HTML replay error pages.
- Compute SHA-256 for all downloaded content.
- Store content hash and byte count in SQLite.

For HTML, additionally:

- Detect if page title/body indicates unavailable capture.
- Preserve original HTML before aggressive rewriting.
- Write normalized recovered HTML separately only if rewriting is performed.

### File Naming

Use deterministic paths to make repeated runs stable.

Examples:

```text
https://kyledurepos.com/                  -> recovered/kyledurepos.com/index.html
https://kyledurepos.com/about             -> recovered/kyledurepos.com/about/index.html
https://kyledurepos.com/about/            -> recovered/kyledurepos.com/about/index.html
https://kyledurepos.com/css/site.css      -> recovered/kyledurepos.com/css/site.css
https://kyledurepos.com/page?id=123       -> recovered/kyledurepos.com/page__q_202cb962.html
```

Use a short hash of the query string where needed.

## Minimal Implementation Skeleton

### Fetch With Backoff

```python
import asyncio
import random
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
    except Exception:
        return None


def backoff_delay(attempt: int, base: float = 2.0, cap: float = 300.0) -> float:
    delay = min(cap, base * (2 ** max(0, attempt - 1)))
    return delay * random.uniform(0.5, 1.5)


async def fetch_with_backoff(client, url: str, max_attempts: int = 5):
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = await client.get(url, timeout=30.0)
            if response.status_code not in RETRYABLE_STATUSES:
                return response

            retry_after = retry_after_seconds(response.headers.get("Retry-After"))
            delay = retry_after if retry_after is not None else backoff_delay(attempt)
            delay = min(300.0, delay) * random.uniform(0.9, 1.1)

            if attempt == max_attempts:
                return response

            await asyncio.sleep(delay)
        except Exception as exc:
            last_exc = exc
            if attempt == max_attempts:
                raise
            await asyncio.sleep(backoff_delay(attempt))
    raise last_exc
```

For the actual recovery pipeline, persist retry decisions to SQLite instead of only sleeping inside the worker. The in-memory sleep version is acceptable for a small helper but less robust for resumability.

### SQLite Job Claim Pattern

Use a transaction to claim a small batch of due jobs.

```sql
BEGIN IMMEDIATE;

SELECT id
FROM fetch_jobs
WHERE status IN ('pending', 'retry_wait')
  AND (next_attempt_at IS NULL OR next_attempt_at <= CURRENT_TIMESTAMP)
ORDER BY priority ASC, id ASC
LIMIT 25;

UPDATE fetch_jobs
SET status = 'in_progress',
    started_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE id IN (...);

COMMIT;
```

In Python, avoid sharing one SQLite cursor across workers. Either use one short-lived connection per operation or a small DB access layer with serialized writes.

## Risks and Mitigations

### Risk: Internet Archive Rate Limiting

Mitigation:

- Keep CDX concurrency at 1.
- Keep content concurrency initially at 3 to 5.
- Persist retry schedule.
- Respect `Retry-After`.

### Risk: Incomplete CDX Discovery

Mitigation:

- Query both apex and `www` hostnames.
- Parse recovered HTML/CSS for additional assets.
- Support per-URL CDX lookup when a referenced asset was not found in bulk discovery.

### Risk: Wayback Error Pages Saved as Site Content

Mitigation:

- Validate content type and body signatures.
- Check file magic bytes for binary assets.
- Store HTTP status, MIME type, hash, and byte count.

### Risk: Duplicate or Conflicting Output Files

Mitigation:

- Use deterministic path mapping.
- Include query hash suffixes.
- Compare SHA-256 before overwriting.
- Store `output_path` and `content_sha256` in SQLite.

### Risk: Interrupted Runs

Mitigation:

- SQLite WAL state DB.
- Stale `in_progress` recovery on startup.
- Idempotent inserts.
- Durable retry schedule.

## Final Recommendation

Build the `kyledurepos.com` recovery automation as a Python async pipeline with SQLite WAL-backed state. Use conservative, separate rate controls for CDX and content fetches, explicit 429 handling with persisted exponential backoff, JSONL structured logs, and end-of-run summary reports. Start in a virtualenv for speed and simplicity. Add Docker only after the command interface and dependency set stabilize.
