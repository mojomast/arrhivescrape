# Pythonic Async Wayback Recovery Pipeline Spec

Target site: `kyledurepos.com`

Serve target: `pwned.ussyco.de` via Tailscale reverse proxy to local Caddy static hosting

Spec output: `/home/mojo/projects/archivebackup/spec-pythonic-async.md`

## Decision

Build a custom Python async recovery pipeline using `asyncio`, `httpx.AsyncClient`, `asyncio.Semaphore`, a custom CDX client with `resumeKey` pagination, and a SQLite WAL state database. The pipeline discovers Wayback captures through CDX, deduplicates first with `collapse=digest`, downloads every selected content object through Wayback `id_` replay URLs, computes SHA256 over on-disk bytes, writes a static mirror tree, and serves that tree with Caddy on loopback behind `tailscale serve` or `tailscale funnel`.

This design intentionally avoids Scrapy, `waybackpack`, `wget --mirror`, server-side dynamic rendering, and application runtime hosting. The output is static files only.

## Hard Constraints

- CDX discovery must use `collapse=digest` for the primary discovery pass.
- Local deduplication must compute SHA256 on the exact bytes written to disk.
- All content fetch URLs must use the Wayback `id_` modifier: `https://web.archive.org/web/{timestamp}id_/{original_url}`.
- CDX API traffic must be sequential with `<= 1` request per second and a practical ceiling of about `60` requests per minute.
- CDX and content fetches must use exponential backoff on `429`; `Retry-After` must be honored when present.
- The recovered site must be static output only under `recovered/kyledurepos.com/site/`.
- The exposed service target is `pwned.ussyco.de`, reached through Tailscale reverse proxying to local Caddy.
- Missing files must return `404`; no SPA fallback to `index.html` is allowed.

## Architecture

```text
                         Internet Archive
                +-------------------------------+
                | CDX API                       |
                | /cdx?...collapse=digest       |
                +---------------+---------------+
                                ^
                                | <= 1 req/sec, resumeKey pages
                                v
+-------------------+    +------+-------+      +-------------------+
| archive_recovery  |    | CDX client   |----->| SQLite WAL state  |
| CLI               |--->| httpx async  |      | captures/jobs     |
+---------+---------+    +------+-------+      +---------+---------+
          |                     |                        ^
          | enqueue jobs        | selected captures      |
          v                     v                        |
+---------+---------+    +------+------------------------+------+
| async scheduler   |--->| content workers                     |
| SQLite queue      |    | httpx + Semaphore + backoff          |
+---------+---------+    | GET /web/{ts}id_/{original_url}     |
          |              +-----------------+-------------------+
          |                                |
          v                                v
+---------+---------+              +-------+-------------------+
| path mapper       |              | dedup + postprocess       |
| URL -> site path  |              | raw SHA256, final SHA256  |
+---------+---------+              +-------+-------------------+
          |                                |
          v                                v
+---------+--------------------------------+-------------------+
| recovered/kyledurepos.com/                                   |
|   site/                 static mirror tree                    |
|   manifest.jsonl        URL/capture/output/hash manifest       |
|   duplicates.jsonl      alias and duplicate records            |
|   selection-report.md   recovery summary                       |
+-----------------------------+--------------------------------+
                              |
                              v
                 +------------+-------------+
                 | Caddy on 127.0.0.1:8080 |
                 | static file server       |
                 +------------+-------------+
                              |
                              v
                 +------------+-------------+
                 | tailscale serve/funnel   |
                 | pwned.ussyco.de          |
                 +--------------------------+
```

## Repository Layout

```text
/home/mojo/projects/archivebackup/
  pyproject.toml
  archive_recovery/
    __init__.py
    cli.py
    config.py
    cdx.py
    db.py
    dedup.py
    fetch.py
    html.py
    logging_json.py
    paths.py
    rate_limit.py
    report.py
    types.py
  configs/
    kyledurepos.com.toml
  data/
    kyledurepos.sqlite3
  logs/
    kyledurepos-recovery.jsonl
  recovered/
    kyledurepos.com/
      site/
      manifest.jsonl
      duplicates.jsonl
      selection-report.md
  Caddyfile
```

## Python Runtime And Dependencies

Use Python `3.12` or newer.

```toml
[project]
name = "archive-recovery"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "httpx>=0.27",
  "aiosqlite>=0.20",
  "beautifulsoup4>=4.12",
  "lxml>=5.0",
  "tinycss2>=1.3"
]

[project.scripts]
archive-recovery = "archive_recovery.cli:main"
```

The implementation must stream binary responses as bytes and must never decode non-text assets as strings.

## Site Configuration

`configs/kyledurepos.com.toml`:

```toml
[site]
domain = "kyledurepos.com"
canonical_host = "kyledurepos.com"
hosts = ["kyledurepos.com", "www.kyledurepos.com"]
output_root = "recovered/kyledurepos.com"
site_root = "recovered/kyledurepos.com/site"

[cdx]
endpoint = "https://web.archive.org/cdx"
match_type = "domain"
fields = ["timestamp", "original", "mimetype", "statuscode", "digest", "length"]
filters = ["statuscode:200"]
collapse = "digest"
limit = 1000
show_resume_key = true
min_interval_seconds = 1.05
max_attempts = 5
base_backoff_seconds = 5
max_backoff_seconds = 300

[fetch]
content_concurrency = 4
per_host_concurrency = 4
timeout_seconds = 30
max_attempts = 5
base_backoff_seconds = 2
max_backoff_seconds = 300
user_agent = "archivebackup-kyledurepos-recovery/0.1 (+https://pwned.ussyco.de)"

[state]
sqlite_path = "data/kyledurepos.sqlite3"
stale_in_progress_minutes = 30

[logging]
jsonl_path = "logs/kyledurepos-recovery.jsonl"
summary_path = "recovered/kyledurepos.com/selection-report.md"
```

## Module Breakdown

`archive_recovery.cli`

Defines the command interface:

```text
archive-recovery init --config configs/kyledurepos.com.toml
archive-recovery discover --config configs/kyledurepos.com.toml
archive-recovery enqueue --config configs/kyledurepos.com.toml
archive-recovery fetch --config configs/kyledurepos.com.toml
archive-recovery report --config configs/kyledurepos.com.toml
archive-recovery run --config configs/kyledurepos.com.toml
```

`run` performs `init`, `discover`, `enqueue`, `fetch`, and `report` in order. Commands are idempotent.

`archive_recovery.config`

Loads TOML config, resolves relative paths from the project root, validates all hard constraints, and exposes typed settings.

`archive_recovery.cdx`

Custom CDX client using `httpx.AsyncClient`. It builds one stable query per site scope, requests `output=json`, `fl=timestamp,original,mimetype,statuscode,digest,length`, `filter=statuscode:200`, `collapse=digest`, `limit=1000`, `showResumeKey=true`, and paginates with `resumeKey` until exhausted. The client persists the current query fingerprint and latest resume key in SQLite after every successful page.

`archive_recovery.rate_limit`

Provides an async interval limiter for CDX and semaphores for content downloads. CDX uses concurrency `1` and waits at least `1.05` seconds between request starts.

`archive_recovery.db`

Owns SQLite initialization, short transactions, idempotent inserts, job claiming, retry scheduling, stale job recovery, and summary queries. It enables WAL pragmas on every connection.

`archive_recovery.fetch`

Implements the async scheduler and content workers. Every content URL is constructed with `id_`. Workers stream to temporary files, validate response status and body, compute hashes, atomically move completed files, and update job state.

`archive_recovery.paths`

Maps original URLs to deterministic local paths. Apex and `www` are folded into one canonical tree. Fragments are dropped from file identity. Query strings are preserved in the manifest and added to filenames only when needed to avoid content conflicts.

`archive_recovery.dedup`

Implements CDX digest skip decisions, SHA256 on-disk deduplication, duplicate alias recording, and collision checks.

`archive_recovery.html`

Performs conservative parser-based HTML cleanup only after `id_` download. It removes known Wayback toolbar/script/style artifacts, rewrites Wayback-wrapped internal URLs to local paths, preserves external URLs, and leaves missing assets visible as broken links rather than inventing fallback content.

`archive_recovery.logging_json`

Writes JSONL events for discovery pages, job state transitions, retries, successes, failures, duplicate skips, and report summaries.

`archive_recovery.report`

Writes `selection-report.md` with counts by status, MIME type, hash, duplicate class, and unresolved failures.

`archive_recovery.types`

Contains dataclasses or typed dictionaries for CDX rows, captures, URL records, jobs, fetch results, and dedup decisions.

## CDX Client Behavior

Primary query:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&collapse=digest&limit=1000&showResumeKey=true
```

The CDX client must keep all query parameters identical while using a returned `resumeKey`. It must not reuse a resume key after changing `url`, `matchType`, `filter`, `fl`, `collapse`, date bounds, or `limit`.

Response parsing rules:

- Accept JSON output where the first row is a field header.
- Accept JSON output where rows are already data rows matching the requested field order.
- Extract a resume key from the CDX response shape used by `showResumeKey=true`; if no new resume key is present, the traversal is complete.
- Persist every capture row before requesting the next page.
- Treat empty data rows without a resume key as completion.

CDX retry rules:

- Retry `429`, `500`, `502`, `503`, `504`, network timeouts, and connection resets.
- On `429`, honor `Retry-After` if present.
- Otherwise back off with `min(max_backoff, base * 2 ** (attempt - 1))` and jitter `0.5x` to `1.5x`.
- CDX attempts are capped at `5`; after that, store the failed page state and stop discovery with a non-zero command exit.
- Never exceed one CDX request per second.

## SQLite Schema DDL

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS cdx_queries (
  id INTEGER PRIMARY KEY,
  site TEXT NOT NULL,
  query_fingerprint TEXT NOT NULL UNIQUE,
  query_url TEXT NOT NULL,
  resume_key TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  pages_fetched INTEGER NOT NULL DEFAULT 0,
  rows_inserted INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  started_at TEXT,
  finished_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS captures (
  id INTEGER PRIMARY KEY,
  original_url TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  mimetype TEXT,
  statuscode INTEGER,
  digest TEXT NOT NULL,
  length INTEGER,
  source_query_id INTEGER REFERENCES cdx_queries(id) ON DELETE SET NULL,
  discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(original_url, timestamp, digest)
);

CREATE INDEX IF NOT EXISTS idx_captures_original_url ON captures(original_url);
CREATE INDEX IF NOT EXISTS idx_captures_digest ON captures(digest);
CREATE INDEX IF NOT EXISTS idx_captures_timestamp ON captures(timestamp);

CREATE TABLE IF NOT EXISTS urls (
  id INTEGER PRIMARY KEY,
  original_url TEXT NOT NULL UNIQUE,
  normalized_url TEXT NOT NULL,
  canonical_host TEXT NOT NULL,
  url_path TEXT NOT NULL,
  query TEXT,
  fragment TEXT,
  inferred_type TEXT NOT NULL DEFAULT 'unknown',
  priority INTEGER NOT NULL DEFAULT 100,
  discovered_from TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_urls_priority ON urls(priority, id);

CREATE TABLE IF NOT EXISTS selected_captures (
  id INTEGER PRIMARY KEY,
  url_id INTEGER NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
  capture_id INTEGER NOT NULL REFERENCES captures(id) ON DELETE CASCADE,
  cdx_digest TEXT NOT NULL,
  selection_rank INTEGER NOT NULL DEFAULT 1,
  selection_reason TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(url_id, capture_id)
);

CREATE INDEX IF NOT EXISTS idx_selected_url_rank ON selected_captures(url_id, selection_rank);
CREATE INDEX IF NOT EXISTS idx_selected_digest ON selected_captures(cdx_digest);

CREATE TABLE IF NOT EXISTS fetch_jobs (
  id INTEGER PRIMARY KEY,
  url_id INTEGER NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
  capture_id INTEGER NOT NULL REFERENCES captures(id) ON DELETE CASCADE,
  job_type TEXT NOT NULL DEFAULT 'content',
  archive_url TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  priority INTEGER NOT NULL DEFAULT 100,
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  last_error TEXT,
  http_status INTEGER,
  response_mimetype TEXT,
  temp_path TEXT,
  output_path TEXT,
  raw_sha256 TEXT,
  final_sha256 TEXT,
  bytes_downloaded INTEGER,
  bytes_written INTEGER,
  duplicate_of_job_id INTEGER REFERENCES fetch_jobs(id) ON DELETE SET NULL,
  started_at TEXT,
  finished_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(url_id, capture_id, job_type)
);

CREATE INDEX IF NOT EXISTS idx_fetch_jobs_due
ON fetch_jobs(status, next_attempt_at, priority, id);

CREATE INDEX IF NOT EXISTS idx_fetch_jobs_capture ON fetch_jobs(capture_id);
CREATE INDEX IF NOT EXISTS idx_fetch_jobs_final_sha ON fetch_jobs(final_sha256);

CREATE TABLE IF NOT EXISTS output_files (
  id INTEGER PRIMARY KEY,
  final_sha256 TEXT NOT NULL UNIQUE,
  canonical_output_path TEXT NOT NULL UNIQUE,
  bytes_written INTEGER NOT NULL,
  mimetype TEXT,
  first_job_id INTEGER NOT NULL REFERENCES fetch_jobs(id) ON DELETE RESTRICT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS output_aliases (
  id INTEGER PRIMARY KEY,
  job_id INTEGER NOT NULL REFERENCES fetch_jobs(id) ON DELETE CASCADE,
  output_file_id INTEGER NOT NULL REFERENCES output_files(id) ON DELETE CASCADE,
  requested_output_path TEXT NOT NULL,
  alias_reason TEXT NOT NULL,
  original_url TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  cdx_digest TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(job_id, requested_output_path)
);

CREATE TABLE IF NOT EXISTS retry_events (
  id INTEGER PRIMARY KEY,
  job_id INTEGER REFERENCES fetch_jobs(id) ON DELETE CASCADE,
  query_id INTEGER REFERENCES cdx_queries(id) ON DELETE CASCADE,
  operation TEXT NOT NULL,
  attempt INTEGER NOT NULL,
  http_status INTEGER,
  error TEXT,
  retry_after_seconds REAL,
  next_attempt_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Allowed `fetch_jobs.status` values:

```text
pending
in_progress
retry_wait
succeeded
failed
skipped_duplicate
skipped_invalid
```

Startup resume behavior:

- Set stale `in_progress` jobs older than `stale_in_progress_minutes` back to `pending`.
- Claim only `pending` jobs or `retry_wait` jobs whose `next_attempt_at <= CURRENT_TIMESTAMP`.
- Never delete succeeded, failed, or skipped jobs during normal operation.
- Use uniqueness constraints for all enqueue operations.

## Capture Selection

The primary CDX pass is already collapsed by digest. Selection still needs deterministic ordering because the same digest can appear under different original URLs and timestamps.

For each normalized URL identity:

1. Prefer `statuscode = 200`.
2. Prefer a MIME type consistent with the URL extension.
3. Prefer non-empty `length` where present.
4. Prefer the newest timestamp for latest-good composite recovery.
5. Prefer canonical host `kyledurepos.com` over `www.kyledurepos.com` when all else is equal.

For duplicate CDX digests across multiple URL identities, enqueue only the best representative for download unless the URL path is semantically important for site navigation. Preserve the skipped URL-to-digest relationship in `output_aliases` after SHA256 confirms byte identity.

## Archive URL Construction

All content fetches use exactly this shape:

```python
def archive_content_url(timestamp: str, original_url: str) -> str:
    return f"https://web.archive.org/web/{timestamp}id_/{original_url}"
```

No content worker may fetch plain replay URLs such as `https://web.archive.org/web/{timestamp}/{original_url}`. The same `id_` rule applies to HTML, CSS, JavaScript, images, fonts, PDFs, JSON, XML, media, and unknown binary content.

## Async Worker Design

Concurrency defaults:

```text
CDX concurrency: 1
CDX minimum interval: 1.05 seconds between request starts
Content concurrency: 4
Per-host content concurrency: 4
HTTP timeout: 30 seconds
Max attempts: 5
Content base backoff: 2 seconds
CDX base backoff: 5 seconds
Max backoff: 300 seconds
Jitter: enabled
```

Scheduler behavior:

```python
async def scheduler(db, queue, stop_event):
    while not stop_event.is_set():
        jobs = await db.claim_due_jobs(limit=50)
        if not jobs:
            await asyncio.sleep(1.0)
            continue
        for job in jobs:
            await queue.put(job)
```

Content worker behavior:

```python
async def content_worker(name, db, queue, client, content_sem):
    while True:
        job = await queue.get()
        try:
            async with content_sem:
                await fetch_one_job(db, client, job)
        finally:
            queue.task_done()
```

Fetch behavior:

```python
async def fetch_one_job(db, client, job):
    await db.mark_started(job.id)
    started = monotonic()

    try:
        response = await client.get(job.archive_url, follow_redirects=True, timeout=job.timeout)
    except RETRYABLE_NETWORK_EXCEPTIONS as exc:
        await db.schedule_retry(job.id, error=str(exc), delay=backoff(job.attempts + 1))
        return

    if response.status_code in RETRYABLE_STATUSES:
        delay = retry_after_or_backoff(response, job.attempts + 1)
        await db.schedule_retry(job.id, http_status=response.status_code, delay=delay)
        return

    if response.status_code != 200:
        await db.mark_failed(job.id, http_status=response.status_code, error="non-200 content response")
        return

    temp_path, raw_sha256, bytes_downloaded = await stream_response_to_temp_file(response)
    final_path, final_sha256, bytes_written, duplicate = await process_and_dedup(job, temp_path)

    if duplicate:
        await db.mark_skipped_duplicate(job.id, duplicate_of_job_id=duplicate.job_id, final_sha256=final_sha256)
    else:
        await db.mark_succeeded(
            job.id,
            http_status=200,
            response_mimetype=response.headers.get("content-type"),
            output_path=final_path,
            raw_sha256=raw_sha256,
            final_sha256=final_sha256,
            bytes_downloaded=bytes_downloaded,
            bytes_written=bytes_written,
            duration_ms=int((monotonic() - started) * 1000),
        )
```

Database writes must be short. No transaction may remain open while awaiting network I/O.

## Rate Limiting And Backoff

Retryable HTTP statuses:

```text
429, 500, 502, 503, 504
```

Normally non-retryable statuses:

```text
400, 401, 403, 404, 410
```

Backoff formula:

```python
def backoff_delay(attempt: int, base: float, cap: float) -> float:
    raw = min(cap, base * (2 ** max(0, attempt - 1)))
    return raw * random.uniform(0.5, 1.5)
```

`Retry-After` parsing:

```python
def retry_after_seconds(header: str | None) -> float | None:
    if not header:
        return None
    value = header.strip()
    if value.isdigit():
        return min(300.0, float(value))
    retry_at = parsedate_to_datetime(value)
    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    return min(300.0, max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds()))
```

When `429` occurs, schedule a durable retry in SQLite. Do not spin in memory and do not immediately requeue the job.

## Path Mapping

Canonicalization rules:

- Lowercase scheme and host.
- Fold `www.kyledurepos.com` into `kyledurepos.com` unless SHA256 proves content conflict that requires a distinct collision path.
- Drop URL fragments from file identity.
- Preserve query strings in SQLite and manifests.
- Map `/` to `index.html`.
- Map `/about` and `/about/` with HTML MIME type to `about/index.html`.
- Preserve asset extensions such as `.css`, `.js`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`, `.ico`, `.woff`, `.woff2`, `.ttf`, `.otf`, `.pdf`, `.json`, `.xml`, `.txt`, `.mp4`, `.webm`, `.mp3`, `.wav`.
- Replace unsafe filesystem characters with `_`.
- Never overwrite a different existing output file. If the target path is already owned by a different final SHA256, append `__u_<8-char-url-sha256>` before the extension.

Examples:

```text
https://kyledurepos.com/                  -> recovered/kyledurepos.com/site/index.html
https://www.kyledurepos.com/              -> recovered/kyledurepos.com/site/index.html
https://kyledurepos.com/about             -> recovered/kyledurepos.com/site/about/index.html
https://kyledurepos.com/about/            -> recovered/kyledurepos.com/site/about/index.html
https://kyledurepos.com/css/site.css      -> recovered/kyledurepos.com/site/css/site.css
https://kyledurepos.com/app.css?v=123     -> recovered/kyledurepos.com/site/app__q_a665a459.css if content differs
https://kyledurepos.com/page?id=123       -> recovered/kyledurepos.com/site/page__q_a665a459/index.html if content differs
```

## Dedup Logic Pseudocode

```python
def select_download_jobs(captures):
    seen_cdx_digests = set()
    for capture in sorted(captures, key=selection_sort_key):
        url_identity = normalize_url_identity(capture.original_url, capture.mimetype)
        upsert_url(url_identity)

        if capture.digest in seen_cdx_digests:
            record_cdx_alias(
                original_url=capture.original_url,
                timestamp=capture.timestamp,
                cdx_digest=capture.digest,
                reason="duplicate_cdx_digest"
            )
            continue

        seen_cdx_digests.add(capture.digest)
        enqueue_fetch_job(
            original_url=capture.original_url,
            timestamp=capture.timestamp,
            archive_url=f"https://web.archive.org/web/{capture.timestamp}id_/{capture.original_url}",
            cdx_digest=capture.digest,
        )


async def process_and_dedup(job, temp_path):
    raw_sha256 = sha256_file(temp_path)
    requested_output_path = map_url_to_output_path(job.original_url, job.mimetype)

    if is_html(job.mimetype, temp_path):
        final_bytes = clean_html_bytes(temp_path, base_url=job.original_url)
        final_sha256 = sha256_bytes(final_bytes)
        candidate_path = requested_output_path
    else:
        final_sha256 = raw_sha256
        final_bytes = None
        candidate_path = requested_output_path

    existing_by_hash = db.lookup_output_file(final_sha256)
    if existing_by_hash:
        db.insert_output_alias(
            job_id=job.id,
            output_file_id=existing_by_hash.id,
            requested_output_path=requested_output_path,
            alias_reason="same_final_sha256",
            original_url=job.original_url,
            timestamp=job.timestamp,
            cdx_digest=job.cdx_digest,
        )
        delete_temp(temp_path)
        return DedupResult(
            output_path=existing_by_hash.canonical_output_path,
            raw_sha256=raw_sha256,
            final_sha256=final_sha256,
            duplicate=True,
            duplicate_of_job_id=existing_by_hash.first_job_id,
        )

    owner = db.lookup_output_path_owner(candidate_path)
    if owner and owner.final_sha256 != final_sha256:
        candidate_path = append_url_hash_suffix(candidate_path, job.original_url)

    ensure_parent_directory(candidate_path)
    if final_bytes is None:
        atomic_move(temp_path, candidate_path)
        bytes_written = file_size(candidate_path)
    else:
        atomic_write_bytes(candidate_path, final_bytes)
        delete_temp(temp_path)
        bytes_written = len(final_bytes)

    output_file_id = db.insert_output_file(
        final_sha256=final_sha256,
        canonical_output_path=candidate_path,
        bytes_written=bytes_written,
        mimetype=job.mimetype,
        first_job_id=job.id,
    )
    db.insert_output_alias(
        job_id=job.id,
        output_file_id=output_file_id,
        requested_output_path=requested_output_path,
        alias_reason="canonical",
        original_url=job.original_url,
        timestamp=job.timestamp,
        cdx_digest=job.cdx_digest,
    )
    return DedupResult(
        output_path=candidate_path,
        raw_sha256=raw_sha256,
        final_sha256=final_sha256,
        duplicate=False,
        duplicate_of_job_id=None,
    )
```

## HTML Cleanup And Link Rewriting

HTML is downloaded with `id_` like every other content type. Cleanup must be conservative:

- Remove nodes with `id="wm-ipp"`.
- Remove scripts whose `src` contains `/static/js/ait-client-rewrite.js`, `/static/js/wbhack.js`, or other known Wayback replay paths.
- Remove stylesheets whose `href` contains `/static/css/banner-styles.css` or `/static/css/iconochive.css`.
- Remove comments exactly matching Wayback toolbar begin/end markers.
- Rewrite `https://web.archive.org/web/<timestamp><modifier>/<url>` and `/web/<timestamp><modifier>/<url>` when `<url>` targets `kyledurepos.com` or `www.kyledurepos.com`.
- Preserve external third-party URLs.
- Preserve anchors and fragments after local path normalization.
- Do not remove arbitrary scripts, arbitrary comments, analytics snippets, or site code.

Wayback rewrite examples:

```text
https://web.archive.org/web/20240301000000id_/https://kyledurepos.com/about/
-> /about/

/web/20240301000000im_/https://kyledurepos.com/assets/logo.png
-> /assets/logo.png

https://web.archive.org/web/20240301000000js_/https://kyledurepos.com/app.js?v=2
-> /app__q_<hash>.js when the query variant is distinct
```

## Static Hosting

The recovered site is served from:

```text
/home/mojo/projects/archivebackup/recovered/kyledurepos.com/site
```

The local Caddy server binds to loopback. Tailscale handles reverse proxy exposure for `pwned.ussyco.de`.

Full `Caddyfile`:

```caddyfile
{
    auto_https off
}

http://127.0.0.1:8080 {
    root * /home/mojo/projects/archivebackup/recovered/kyledurepos.com/site

    encode zstd gzip

    header {
        X-Content-Type-Options nosniff
        Referrer-Policy no-referrer-when-downgrade
    }

    try_files {path} {path}/index.html {path}.html

    file_server
}
```

This Caddyfile deliberately disables Caddy public ACME management because Tailscale terminates HTTPS for the exposed endpoint. If public DNS is later pointed directly at this machine and ports `80` and `443` are reachable, replace the site label with `pwned.ussyco.de` and remove `auto_https off`; that is not the default for this spec.

Start local Caddy:

```bash
caddy run --config /home/mojo/projects/archivebackup/Caddyfile
```

Private tailnet exposure:

```bash
tailscale serve --bg --https=443 http://127.0.0.1:8080
tailscale serve status
```

Public Funnel exposure, only if intentionally enabled for the tailnet and appropriate for the recovered archive:

```bash
tailscale funnel --bg --https=443 http://127.0.0.1:8080
tailscale funnel status
```

Reset Tailscale serving state:

```bash
tailscale serve reset
```

Hostname requirement:

- `pwned.ussyco.de` must resolve through the chosen Tailscale path.
- For private access, configure tailnet DNS, split DNS, or a CNAME pattern supported by the tailnet so `pwned.ussyco.de` reaches the serving node.
- For public access, enable Tailscale Funnel/custom domain support for `pwned.ussyco.de` or point public DNS directly at the host and switch Caddy to direct public HTTPS.

## Build And Run Procedure

```bash
cd /home/mojo/projects/archivebackup
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e .
archive-recovery init --config configs/kyledurepos.com.toml
archive-recovery discover --config configs/kyledurepos.com.toml
archive-recovery enqueue --config configs/kyledurepos.com.toml
archive-recovery fetch --config configs/kyledurepos.com.toml
archive-recovery report --config configs/kyledurepos.com.toml
```

One-command run:

```bash
archive-recovery run --config configs/kyledurepos.com.toml
```

## Validation

Pipeline validation:

```bash
sqlite3 data/kyledurepos.sqlite3 'PRAGMA journal_mode;'
sqlite3 data/kyledurepos.sqlite3 'SELECT status, COUNT(*) FROM fetch_jobs GROUP BY status;'
sqlite3 data/kyledurepos.sqlite3 'SELECT COUNT(DISTINCT digest) FROM captures;'
sqlite3 data/kyledurepos.sqlite3 'SELECT COUNT(DISTINCT final_sha256) FROM fetch_jobs WHERE final_sha256 IS NOT NULL;'
```

Static hosting validation:

```bash
curl -I http://127.0.0.1:8080/
curl -I http://127.0.0.1:8080/index.html
curl -I http://127.0.0.1:8080/about
curl -I http://127.0.0.1:8080/missing-file
```

Expected hosting behavior:

- Existing exact files return `200`.
- Extensionless HTML paths backed by `path/index.html` or `path.html` return `200`.
- Missing files return `404`.
- Asset MIME types are served by Caddy automatically.
- Directory browsing is disabled for exposed service.

## Logging And Reports

JSONL log path:

```text
logs/kyledurepos-recovery.jsonl
```

Required event names:

```text
cdx_page_started
cdx_page_succeeded
cdx_retry_scheduled
cdx_completed
job_enqueued
fetch_started
fetch_retry_scheduled
fetch_succeeded
fetch_failed
fetch_skipped_duplicate
output_collision_resolved
report_written
```

Each fetch event must include:

```json
{
  "event": "fetch_succeeded",
  "job_id": 42,
  "original_url": "https://kyledurepos.com/",
  "archive_url": "https://web.archive.org/web/20200101000000id_/https://kyledurepos.com/",
  "timestamp": "20200101000000",
  "attempt": 1,
  "http_status": 200,
  "mimetype": "text/html",
  "bytes_downloaded": 18422,
  "bytes_written": 17891,
  "raw_sha256": "...",
  "final_sha256": "...",
  "output_path": "recovered/kyledurepos.com/site/index.html",
  "duration_ms": 812
}
```

Report path:

```text
recovered/kyledurepos.com/selection-report.md
```

The report must include:

- Total CDX pages fetched.
- Total captures discovered.
- Total unique CDX digests discovered.
- Total jobs by status.
- HTTP status distribution.
- MIME type distribution.
- Bytes downloaded and bytes written.
- Unique final SHA256 count.
- Duplicate aliases count.
- Output path collision count.
- Top failed URLs with last error.
- Confirmation that every content fetch URL used `id_`.

## Non-Goals

- No dynamic application server.
- No server-side rendering.
- No live crawling outside Internet Archive unless a later phase explicitly authorizes it.
- No JavaScript execution for asset discovery.
- No catch-all rewrite to `/index.html`.
- No plain Wayback replay content fetches.
- No symlink-based public output; aliases live in manifests unless hardlinks are explicitly enabled in a later phase.

## Acceptance Criteria

- `archive-recovery discover` pages through CDX with `resumeKey`, `collapse=digest`, `filter=statuscode:200`, and `<= 1` request per second.
- `archive-recovery fetch` uses only `https://web.archive.org/web/{timestamp}id_/{original_url}` for content.
- Interrupted runs resume from SQLite without refetching succeeded jobs.
- All saved files have SHA256 recorded in SQLite and `manifest.jsonl`.
- Duplicate final SHA256 payloads are represented as aliases rather than repeated physical files by default.
- The mirror exists under `recovered/kyledurepos.com/site/` and contains static files only.
- Caddy serves the mirror from `127.0.0.1:8080` with exact path, directory index, and `.html` fallback behavior.
- `tailscale serve` or `tailscale funnel` exposes the local Caddy service for `pwned.ussyco.de` according to tailnet DNS/Funnel configuration.
