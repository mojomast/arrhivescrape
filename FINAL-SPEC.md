# FINAL SPEC: kyledurepos.com Wayback Recovery

## 1. Executive Summary - what this builds and why these choices

This build recovers `kyledurepos.com` from the Internet Archive Wayback Machine into a static local mirror, then serves that mirror from `/home/mojo/projects/archivebackup/recovered/kyledurepos.com/site` through Caddy on `127.0.0.1:8080` and Tailscale at `pwned.ussyco.de`.

The authoritative implementation is a custom Python async pipeline using `asyncio`, `httpx.AsyncClient`, `aiosqlite`, SQLite WAL state, bounded content workers, CDX `resumeKey` pagination, durable retry scheduling, parser-based HTML cleanup, SHA256 deduplication, structured JSONL logs, and manifest/report output. This is the strongest synthesis because all Phase 2 reviews ranked `spec-pythonic-async.md` first for reliability, maintainability, and production readiness.

Review score tally:

| Spec | Reliability Average | DX Total | Production Average | Combined Tally |
| --- | ---: | ---: | ---: | ---: |
| Minimalist | 7.0 | 30 | 6.6 | 43.6 |
| Pythonic Async | 8.8 | 43 | 7.8 | 59.6 |
| Containerized | 8.0 | 36 | 7.4 | 51.4 |

The final design cherry-picks the best components from all specs: Pythonic Async for the pipeline and state model, Containerized for raw content-addressed audit storage and strict public-root isolation, and Minimalist/hosting research for the simple loopback static-server plus Tailscale exposure pattern. Research conflicts are resolved in favor of the CDX and dedup evidence: the primary discovery pass must use `collapse=digest`, but an alias-preserving supplemental CDX inventory is also required because `collapse=digest` can hide useful URL/timestamp aliases. Every content fetch uses `id_`; plain Wayback replay URLs are forbidden for automated downloads.

Hard constraints preserved:

- Dual-layer deduplication: CDX `collapse=digest` plus SHA256 over on-disk bytes.
- All content fetch URLs use `https://web.archive.org/web/{timestamp}id_/{original_url}`.
- CDX API is sequential at `<= 1` request/second, configured as `1.1` seconds between starts, with an effective ceiling near `54` requests/minute and below the `~60` requests/minute limit.
- `429` uses `Retry-After` when present, otherwise exponential backoff with jitter.
- Public output is static files only.
- Serve target is `pwned.ussyco.de` through Tailscale reverse proxying to local Caddy.

## 2. Architecture Overview - ASCII pipeline diagram end to end

```text
                         Internet Archive
        +------------------------------------------------+
        | CDX API                                        |
        | /cdx?url=kyledurepos.com&matchType=domain      |
        | output=json, collapse=digest, resumeKey pages   |
        +------------------------+-----------------------+
                                 |
                                 | 1 request at a time
                                 | >= 1.1s between starts
                                 v
+----------------------+  writes pages/captures   +----------------------+
| archive-recovery     |-------------------------->| SQLite WAL state     |
| discover             |                           | data/kyledurepos.db  |
+----------+-----------+                           +----------+-----------+
           |                                                  ^
           | supplemental alias inventory                     |
           v                                                  |
+----------+-----------+  selected captures/jobs   +----------+-----------+
| archive-recovery     |-------------------------->| fetch_jobs, aliases  |
| enqueue              |                           | retry_events         |
+----------+-----------+                           +----------+-----------+
           |                                                  ^
           v                                                  |
+----------+-----------+  GET /web/{ts}id_/{url}   +----------+-----------+
| async content        |-------------------------->| raw SHA256 store     |
| workers, concurrency |                           | raw/sha256/ab/hash   |
| 4, backoff/retries   |                           +----------+-----------+
+----------+-----------+                                      |
           |                                                  v
           | raw_sha256, final_sha256              +----------+-----------+
           +-------------------------------------->| postprocess/dedup    |
                                                   | HTML cleanup, links  |
                                                   +----------+-----------+
                                                              |
                                                              v
                                      +-----------------------+------------+
                                      | recovered/kyledurepos.com/         |
                                      | site/ static mirror only            |
                                      | manifest.jsonl, duplicates.jsonl    |
                                      | selection-report.md                 |
                                      +-----------------------+------------+
                                                              |
                                                              v
                                      +-----------------------+------------+
                                      | Caddy 127.0.0.1:8080               |
                                      | exact file, index, .html fallback  |
                                      | missing files remain 404           |
                                      +-----------------------+------------+
                                                              |
                                                              v
                                      +-----------------------+------------+
                                      | Tailscale Serve/Funnel             |
                                      | https://pwned.ussyco.de            |
                                      +------------------------------------+
```

## 3. Component Decision Log - which spec each component came from and why

| Domain | Selected Component | Source Spec | Why |
| --- | --- | --- | --- |
| Orchestration | Python async CLI with `asyncio`, `httpx`, `aiosqlite` | `spec-pythonic-async.md` | Highest reliability, DX, and production score; best fit for retries, queues, and resumability. |
| State | SQLite WAL with CDX cursor, captures, URLs, jobs, outputs, aliases, retry events | `spec-pythonic-async.md` plus review fixes | Durable resume, stale-job recovery, query fingerprinting, and auditable dedup. |
| Primary CDX discovery | Domain-scoped `collapse=digest`, `resumeKey`, `limit=1000` | All specs, strongest in Pythonic Async | Required hard constraint and minimizes duplicate downloads. |
| Alias inventory | Supplemental uncollapsed/domain CDX pass stored for aliases, not extra downloads | Research and review-reliability fix | Research warns `collapse=digest` can hide aliases; this preserves URL/timestamp mapping while still using collapsed primary discovery. |
| Downloader | Async content workers, concurrency `4`, streamed bytes, durable backoff | `spec-pythonic-async.md` | Best binary handling and retry model. |
| Raw storage | `raw/sha256/<first-two>/<sha256>` content-addressed store | `spec-containerized.md` | Best auditability and reprocessing safety without serving raw files. |
| Dedup | CDX digest skip plus raw/final SHA256 output dedup and alias records | Pythonic Async plus Containerized | Meets hard dual-layer dedup and supports HTML cleanup changing final bytes. |
| HTML cleanup | Parser-based removal of known Wayback artifacts and archive URL rewrite | `spec-pythonic-async.md` and `spec-containerized.md` | Required because `id_` reduces but does not eliminate replay artifacts. |
| Path mapping | Canonical mirror tree, `www` folded to apex, query collision hashes | `spec-pythonic-async.md` and `research-dedup.md` | Produces a readable static site while preserving conflicts. |
| Local serving | Caddy on loopback with exact/index/`.html` fallback | `spec-pythonic-async.md` and `research-hosting.md` | Caddy is concise, handles MIME well, and works cleanly behind Tailscale. |
| Serve hardening | Health endpoint, hidden-file deny, cache headers, compression | Production review fixes plus Caddy source | Closes production-review gaps. |
| Tailscale exposure | Host Caddy locally, expose with `tailscale serve` or `tailscale funnel` | `spec-minimalist.md`, `spec-pythonic-async.md`, hosting research | Simpler and less ambiguous than a Tailscale sidecar for this local build. |
| Docker | Not mandatory; optional later | Research orchestration and DX review | Docker is useful after the CLI stabilizes, but virtualenv is faster and less error-prone for first recovery. |

## 4. Phase 1: CDX Discovery - full query strategy, pagination, field selection, output schema

Discovery has two passes.

Primary download-candidate pass:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&collapse=digest&limit=1000&showResumeKey=true
```

Supplemental alias inventory pass:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=urlkey,timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&limit=1000&showResumeKey=true
```

The primary pass satisfies the hard `collapse=digest` constraint and drives download selection. The supplemental pass is not used to duplicate downloads; it preserves URL/timestamp aliases that `collapse=digest` may hide. Both passes use `matchType=domain` so apex, `www`, and subdomain captures are visible. The pipeline also normalizes apex and `www` into one public site tree unless SHA256/content conflict requires a collision path.

Pagination rules:

- Use `limit=1000` and `showResumeKey=true`.
- Keep all query parameters identical between pages.
- Append only URL-encoded `resumeKey=<returned-key>` for the next page.
- Persist each page's rows and resume key before requesting the next page.
- Stop when the page has no data rows and no new resume key.
- CDX concurrency is always `1`.
- Wait at least `1.1` seconds between CDX request starts.
- Retry `429`, `500`, `502`, `503`, `504`, timeout, and connection reset.
- Honor `Retry-After` on `429`; otherwise use `min(300, base * 2 ** (attempt - 1)) * jitter`.

CDX field selection:

| Field | Used For |
| --- | --- |
| `urlkey` | Supplemental alias inventory and URL grouping. |
| `timestamp` | Constructing `id_` replay URLs and selecting newest high-quality captures. |
| `original` | Original URL, path mapping, link rewrite target. |
| `mimetype` | Validation, path inference, binary/text handling. |
| `statuscode` | Primary filter and error matrix context. |
| `digest` | CDX-level dedup and alias grouping. |
| `length` | Sanity validation and snapshot quality scoring. |

CDX JSONL output schema for `logs/cdx-pages.jsonl`:

```json
{
  "event": "cdx_page_succeeded",
  "query_kind": "primary_collapsed",
  "query_fingerprint": "sha256-of-stable-query-without-resumeKey",
  "page_number": 1,
  "resume_key_in": null,
  "resume_key_out": "opaque-cdx-resume-key",
  "rows_seen": 1000,
  "rows_inserted": 997,
  "http_status": 200,
  "duration_ms": 823,
  "requested_at": "2026-06-22T00:00:00Z"
}
```

Capture row schema in SQLite is defined in Section 10. Each CDX row is stored before content fetching begins.

## 5. Phase 2: Download Pipeline - tool, async worker count, rate limiting, id_ usage, file naming, binary handling

Tooling:

- Python `3.12+` CLI package named `archive-recovery`.
- HTTP client: `httpx.AsyncClient(follow_redirects=True)`.
- State: `aiosqlite` with SQLite WAL.
- HTML parser: `beautifulsoup4` with `lxml`.
- CSS parsing: `tinycss2` for URL extraction/audit.

Worker defaults:

```text
CDX concurrency: 1
CDX minimum interval: 1.1 seconds
Content concurrency: 4
Per-host content concurrency: 4
HTTP timeout: 30 seconds
Content max attempts: 5
Content base backoff: 2 seconds
CDX base backoff: 5 seconds
Max backoff: 300 seconds
Jitter: 0.5x to 1.5x
```

Every content URL is constructed exactly as:

```python
def archive_content_url(timestamp: str, original_url: str) -> str:
    return f"https://web.archive.org/web/{timestamp}id_/{original_url}"
```

Forbidden automated fetch form:

```text
https://web.archive.org/web/{timestamp}/{original_url}
```

File naming rules:

- Output root is `recovered/kyledurepos.com/site`.
- `https://kyledurepos.com/` maps to `index.html`.
- HTML `/about` and `/about/` map to `about/index.html`.
- Existing asset extensions are preserved: `.css`, `.js`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`, `.ico`, `.json`, `.xml`, `.txt`, `.pdf`, `.woff`, `.woff2`, `.ttf`, `.otf`, `.mp4`, `.webm`, `.mp3`, `.wav`, `.wasm`, `.avif`.
- Fragments are dropped from file identity and preserved only in rewritten links.
- Query strings are kept in SQLite/manifests. If query-bearing content differs, append `__q_<8-char-sha256-query>` before the extension or before `/index.html` for HTML routes.
- Unsafe filesystem characters are replaced with `_`.
- If a different final SHA256 already owns the intended path, append `__u_<8-char-sha256-normalized-url>` before the extension.

Binary handling:

- Stream responses to temporary files under `tmp/downloads/`; never decode binary content as text.
- Compute `raw_sha256` over the exact downloaded bytes before cleanup.
- Store raw bytes at `raw/sha256/<first-two-hex>/<raw_sha256>`.
- For non-HTML files, `final_sha256 = raw_sha256` unless a safe text post-processing rule applies.
- Validate common binary signatures when possible: PNG, JPEG, GIF, WebP, SVG/XML text, PDF, WOFF, WOFF2, TTF/OTF, MP4/WebM.
- Reject likely Wayback/HTML error bodies for expected CSS, JS, image, font, PDF, and media assets.
- Atomic behavior: write `.part` or temp files first, fsync where practical, then atomically rename into raw store and final site tree.

## 6. Phase 3: Deduplication - SHA256 pass, URL normalization, snapshot selection logic

Deduplication has two mandatory layers.

CDX layer:

- The primary discovery query uses `collapse=digest`.
- The enqueue stage groups candidate captures by CDX `digest`.
- Only the highest-quality representative per digest is fetched by default.
- Supplemental alias inventory rows with the same digest are recorded as aliases and not fetched unless the representative fails validation.

On-disk SHA256 layer:

- Compute `raw_sha256` after download and before any cleanup.
- Compute `final_sha256` over the exact bytes written to the static site tree.
- Keep one canonical physical output per unique `final_sha256` by default.
- Record every URL/capture mapping in `output_aliases` and `manifest.jsonl`.
- Use hardlinks only if a duplicate path is required for navigability; do not use symlinks in public output.

URL normalization:

- Lowercase scheme and host.
- Canonical public host is `kyledurepos.com`.
- Fold `www.kyledurepos.com` into the same tree unless final SHA256 conflict proves distinct content.
- Drop fragments from download identity.
- Preserve query strings through selection; collapse query variants only after SHA256 proves byte identity.
- Normalize duplicate slashes.
- Decode safe percent-encoded characters but never decode path separators or unsafe filesystem characters.

Snapshot selection logic for latest-good composite recovery:

1. Prefer `statuscode = 200`.
2. Prefer MIME type consistent with URL extension or route type.
3. Require non-empty body after fetch.
4. Prefer captures without Wayback error signatures, parked-domain text, bot-check pages, or obvious archive failures.
5. Prefer newest timestamp within the high-quality class.
6. Prefer captures close to the selected homepage timestamp for HTML consistency when quality is tied.
7. Prefer canonical host `kyledurepos.com` over `www.kyledurepos.com` when equivalent.
8. If the selected capture fails validation, try the next candidate from the same normalized URL or same digest alias group.

The default mode is latest-good composite, not point-in-time reconstruction, because the goal is maximum usable static recovery. Point-in-time mode may be added later with an explicit target timestamp.

## 7. Phase 4: Post-Processing - artifact stripping, link rewriting for local serve, MIME audit

HTML post-processing is conservative and parser-based.

Remove only known Wayback artifacts:

- Elements with `id="wm-ipp"`.
- Comments containing `BEGIN WAYBACK TOOLBAR INSERT` through `END WAYBACK TOOLBAR INSERT`.
- Scripts whose `src` contains `/static/js/ait-client-rewrite.js`, `/static/js/wbhack.js`, `/static/js/playback.js`, `/static/js/timestamp.js`, or `/static/js/bundle-playback.js`.
- Stylesheets whose `href` contains `/static/css/banner-styles.css` or `/static/css/iconochive.css`.
- Inline replay bootstrap code that references `__wm`, `wbinfo`, or Wayback replay setup, only when matched to known Wayback patterns.

Do not remove arbitrary site scripts, analytics snippets, comments, or inline styles.

Rewrite URL-bearing attributes:

- HTML attributes: `href`, `src`, `srcset`, `poster`, `action`.
- Inline CSS URLs in `style` attributes.
- CSS `url(...)` and `@import` in stylesheet files.

Rewrite rules:

- Archive-wrapped URLs targeting `kyledurepos.com` or `www.kyledurepos.com` become local absolute paths rooted at `/`.
- Direct internal URLs targeting apex or `www` become local paths.
- Relative links are resolved against the original page URL and mapped to local paths.
- External third-party URLs remain external unless explicitly recovered in a later build.
- Fragments are preserved after path normalization.
- Missing assets remain broken links; do not invent SPA fallbacks or placeholder files.

Examples:

```text
https://web.archive.org/web/20240301000000id_/https://kyledurepos.com/about/
-> /about/

/web/20240301000000im_/https://kyledurepos.com/assets/logo.png
-> /assets/logo.png

https://web.archive.org/web/20240301000000js_/https://kyledurepos.com/app.js?v=2
-> /app__q_<hash>.js when that query variant has distinct final content
```

MIME audit:

- Store CDX MIME, response `Content-Type`, inferred extension MIME, and final served MIME expectation.
- Flag mismatches where CSS/JS/binary URLs return HTML.
- Flag unknown extensions and default them to `application/octet-stream` at serve time.
- Emit `reports/mime-audit.md` with mismatches, rejected files, and unusual extensions.

## 8. Phase 5: Local Serve Setup - complete server config (not pseudocode), directory structure

Directory structure:

```text
/home/mojo/projects/archivebackup/
  pyproject.toml
  Caddyfile
  configs/
    kyledurepos.com.toml
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
  data/
    kyledurepos.sqlite3
  logs/
    kyledurepos-recovery.jsonl
    cdx-pages.jsonl
  raw/
    sha256/
  tmp/
    downloads/
  reports/
    mime-audit.md
  recovered/
    kyledurepos.com/
      site/
        index.html
      manifest.jsonl
      duplicates.jsonl
      selection-report.md
```

Complete `Caddyfile`:

```caddyfile
{
    auto_https off
    admin off
}

http://127.0.0.1:8080 {
    root * /home/mojo/projects/archivebackup/recovered/kyledurepos.com/site

    encode zstd gzip

    header {
        X-Content-Type-Options nosniff
        Referrer-Policy no-referrer-when-downgrade
        Permissions-Policy "geolocation=(), microphone=(), camera=()"
    }

    @html path *.html /
    header @html Cache-Control "no-cache, max-age=0, must-revalidate"

    @static path *.css *.js *.png *.jpg *.jpeg *.gif *.webp *.svg *.ico *.woff *.woff2 *.ttf *.otf *.pdf *.json *.xml *.txt *.mp4 *.webm *.mp3 *.wav *.wasm *.avif
    header @static Cache-Control "public, max-age=3600"

    @hidden path */.* .*
    respond @hidden 404

    handle_path /healthz {
        respond "ok\n" 200
    }

    try_files {path} {path}/index.html {path}.html

    file_server
}
```

Local server commands:

```bash
cd /home/mojo/projects/archivebackup
caddy fmt --overwrite Caddyfile
caddy validate --config Caddyfile
caddy run --config /home/mojo/projects/archivebackup/Caddyfile
```

Optional systemd user unit at `~/.config/systemd/user/archivebackup-caddy.service`:

```ini
[Unit]
Description=archivebackup Caddy static server
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/mojo/projects/archivebackup
ExecStart=/usr/bin/caddy run --config /home/mojo/projects/archivebackup/Caddyfile
ExecReload=/usr/bin/caddy reload --config /home/mojo/projects/archivebackup/Caddyfile
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Enable the user service:

```bash
mkdir -p ~/.config/systemd/user
systemctl --user daemon-reload
systemctl --user enable --now archivebackup-caddy.service
systemctl --user status archivebackup-caddy.service
```

Validation:

```bash
curl -I http://127.0.0.1:8080/healthz
curl -I http://127.0.0.1:8080/
curl -I http://127.0.0.1:8080/index.html
curl -I http://127.0.0.1:8080/about
curl -I http://127.0.0.1:8080/__definitely_missing_archivebackup_path__
```

Expected behavior: exact files return `200`, directory index paths return `200` when present, extensionless HTML paths resolve to `path/index.html` or `path.html`, hidden files return `404`, and missing files return `404`.

## 9. Phase 6: Tailscale + pwned.ussyco.de - complete tunnel + DNS config

Tailscale private Serve setup:

```bash
sudo tailscale up
tailscale status
tailscale serve reset
tailscale serve --bg --https=443 http://127.0.0.1:8080
tailscale serve status
```

Public Funnel setup, only if the recovered archive is intended to be public and Funnel/custom-domain policy is enabled:

```bash
tailscale serve reset
tailscale funnel --bg --https=443 http://127.0.0.1:8080
tailscale funnel status
```

Private DNS configuration for `pwned.ussyco.de`:

```text
Record type: A
Name: pwned.ussyco.de
Value: <this-node-Tailscale-IPv4-from-tailscale-ip -4>
Scope: tailnet split DNS or private DNS zone only
```

Get the node address:

```bash
tailscale ip -4
```

Public Funnel/custom-domain DNS configuration when supported by the tailnet:

```text
Record type: CNAME
Name: pwned.ussyco.de
Value: <Tailscale Funnel/custom-domain target shown by tailscale funnel status or tailnet admin>
Proxy/CDN: disabled unless explicitly validated with Tailscale Funnel
```

If Tailscale custom-domain support is unavailable, use the node's assigned `*.ts.net` name for private Serve, or point public DNS directly at this host and switch Caddy to direct public HTTPS. Direct public HTTPS is not the default because the hard serve target for this build is Tailscale reverse proxying.

Preflight checklist before exposing `pwned.ussyco.de`:

- `curl -I http://127.0.0.1:8080/healthz` returns `200`.
- `tailscale status` shows this node connected.
- `tailscale serve status` or `tailscale funnel status` shows HTTPS `443` forwarding to `http://127.0.0.1:8080`.
- DNS for `pwned.ussyco.de` resolves to the selected private Tailscale IP or Funnel/custom-domain target.
- The archive owner accepts the risk of serving recovered active JavaScript. If not, keep access private to the tailnet.

External validation:

```bash
curl -I https://pwned.ussyco.de/healthz
curl -I https://pwned.ussyco.de/
curl -I https://pwned.ussyco.de/__definitely_missing_archivebackup_path__
```

## 10. State DB Schema - SQLite DDL for all tables

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS cdx_queries (
  id INTEGER PRIMARY KEY,
  site TEXT NOT NULL,
  query_kind TEXT NOT NULL,
  query_fingerprint TEXT NOT NULL UNIQUE,
  query_url TEXT NOT NULL,
  resume_key TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  pages_fetched INTEGER NOT NULL DEFAULT 0,
  rows_seen INTEGER NOT NULL DEFAULT 0,
  rows_inserted INTEGER NOT NULL DEFAULT 0,
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  http_status INTEGER,
  last_error TEXT,
  started_at TEXT,
  finished_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cdx_pages (
  id INTEGER PRIMARY KEY,
  query_id INTEGER NOT NULL REFERENCES cdx_queries(id) ON DELETE CASCADE,
  page_number INTEGER NOT NULL,
  resume_key_in TEXT,
  resume_key_out TEXT,
  http_status INTEGER,
  rows_seen INTEGER NOT NULL DEFAULT 0,
  rows_inserted INTEGER NOT NULL DEFAULT 0,
  duration_ms INTEGER,
  fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(query_id, page_number)
);

CREATE TABLE IF NOT EXISTS captures (
  id INTEGER PRIMARY KEY,
  original_url TEXT NOT NULL,
  urlkey TEXT,
  timestamp TEXT NOT NULL,
  mimetype TEXT,
  statuscode INTEGER,
  digest TEXT NOT NULL,
  length INTEGER,
  source_query_id INTEGER REFERENCES cdx_queries(id) ON DELETE SET NULL,
  source_kind TEXT NOT NULL,
  discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(original_url, timestamp, digest, source_kind)
);

CREATE INDEX IF NOT EXISTS idx_captures_original_url ON captures(original_url);
CREATE INDEX IF NOT EXISTS idx_captures_digest ON captures(digest);
CREATE INDEX IF NOT EXISTS idx_captures_timestamp ON captures(timestamp);
CREATE INDEX IF NOT EXISTS idx_captures_source_kind ON captures(source_kind);

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
CREATE INDEX IF NOT EXISTS idx_urls_normalized_url ON urls(normalized_url);

CREATE TABLE IF NOT EXISTS selected_captures (
  id INTEGER PRIMARY KEY,
  url_id INTEGER NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
  capture_id INTEGER NOT NULL REFERENCES captures(id) ON DELETE CASCADE,
  cdx_digest TEXT NOT NULL,
  selection_rank INTEGER NOT NULL DEFAULT 1,
  selection_score INTEGER NOT NULL DEFAULT 0,
  selection_reason TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(url_id, capture_id)
);

CREATE INDEX IF NOT EXISTS idx_selected_url_rank ON selected_captures(url_id, selection_rank);
CREATE INDEX IF NOT EXISTS idx_selected_digest ON selected_captures(cdx_digest);

CREATE TABLE IF NOT EXISTS cdx_aliases (
  id INTEGER PRIMARY KEY,
  selected_capture_id INTEGER REFERENCES selected_captures(id) ON DELETE SET NULL,
  alias_capture_id INTEGER NOT NULL REFERENCES captures(id) ON DELETE CASCADE,
  alias_reason TEXT NOT NULL,
  original_url TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  cdx_digest TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(alias_capture_id, alias_reason)
);

CREATE TABLE IF NOT EXISTS fetch_jobs (
  id INTEGER PRIMARY KEY,
  url_id INTEGER NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
  capture_id INTEGER NOT NULL REFERENCES captures(id) ON DELETE CASCADE,
  job_type TEXT NOT NULL DEFAULT 'content',
  archive_url TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  priority INTEGER NOT NULL DEFAULT 100,
  attempts INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 5,
  next_attempt_at TEXT,
  last_error TEXT,
  http_status INTEGER,
  response_mimetype TEXT,
  temp_path TEXT,
  raw_path TEXT,
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

CREATE INDEX IF NOT EXISTS idx_fetch_jobs_due ON fetch_jobs(status, next_attempt_at, priority, id);
CREATE INDEX IF NOT EXISTS idx_fetch_jobs_capture ON fetch_jobs(capture_id);
CREATE INDEX IF NOT EXISTS idx_fetch_jobs_final_sha ON fetch_jobs(final_sha256);
CREATE INDEX IF NOT EXISTS idx_fetch_jobs_raw_sha ON fetch_jobs(raw_sha256);

CREATE TABLE IF NOT EXISTS raw_objects (
  id INTEGER PRIMARY KEY,
  raw_sha256 TEXT NOT NULL UNIQUE,
  raw_path TEXT NOT NULL UNIQUE,
  bytes_downloaded INTEGER NOT NULL,
  first_job_id INTEGER NOT NULL REFERENCES fetch_jobs(id) ON DELETE RESTRICT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS validation_events (
  id INTEGER PRIMARY KEY,
  job_id INTEGER REFERENCES fetch_jobs(id) ON DELETE CASCADE,
  severity TEXT NOT NULL,
  check_name TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS run_events (
  id INTEGER PRIMARY KEY,
  event TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Allowed `fetch_jobs.status` values: `pending`, `in_progress`, `retry_wait`, `succeeded`, `failed`, `skipped_duplicate`, `skipped_invalid`.

Startup resume behavior:

- Set stale `in_progress` jobs older than `stale_in_progress_minutes` back to `pending`.
- Claim only `pending` jobs or `retry_wait` jobs whose `next_attempt_at <= CURRENT_TIMESTAMP`.
- Never delete succeeded, failed, or skipped jobs during normal operation.
- Use uniqueness constraints for idempotent discovery and enqueue.

## 11. CLI Reference - every command in order, from blank folder to live site

Install OS packages on Ubuntu/Debian:

```bash
cd /home/mojo/projects/archivebackup
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3-pip sqlite3 caddy tailscale ca-certificates curl
```

Create project directories:

```bash
mkdir -p archive_recovery configs data logs raw/sha256 tmp/downloads reports recovered/kyledurepos.com/site
```

Create `pyproject.toml`:

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

Create `configs/kyledurepos.com.toml`:

```toml
[site]
domain = "kyledurepos.com"
canonical_host = "kyledurepos.com"
hosts = ["kyledurepos.com", "www.kyledurepos.com"]
output_root = "recovered/kyledurepos.com"
site_root = "recovered/kyledurepos.com/site"
raw_root = "raw/sha256"
tmp_root = "tmp/downloads"

[cdx]
endpoint = "https://web.archive.org/cdx"
match_type = "domain"
primary_fields = ["timestamp", "original", "mimetype", "statuscode", "digest", "length"]
alias_fields = ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]
filters = ["statuscode:200"]
collapse = "digest"
limit = 1000
show_resume_key = true
min_interval_seconds = 1.1
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
cdx_jsonl_path = "logs/cdx-pages.jsonl"
summary_path = "recovered/kyledurepos.com/selection-report.md"
mime_audit_path = "reports/mime-audit.md"
manifest_path = "recovered/kyledurepos.com/manifest.jsonl"
duplicates_path = "recovered/kyledurepos.com/duplicates.jsonl"
```

Set up Python environment:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Run recovery stages:

```bash
archive-recovery init --config configs/kyledurepos.com.toml
archive-recovery discover --config configs/kyledurepos.com.toml --kind primary-collapsed
archive-recovery discover --config configs/kyledurepos.com.toml --kind alias-inventory
archive-recovery enqueue --config configs/kyledurepos.com.toml
archive-recovery fetch --config configs/kyledurepos.com.toml
archive-recovery postprocess --config configs/kyledurepos.com.toml
archive-recovery report --config configs/kyledurepos.com.toml
```

One-command equivalent:

```bash
archive-recovery run --config configs/kyledurepos.com.toml
```

Inspect state:

```bash
sqlite3 data/kyledurepos.sqlite3 'PRAGMA journal_mode;'
sqlite3 data/kyledurepos.sqlite3 'SELECT status, COUNT(*) FROM fetch_jobs GROUP BY status ORDER BY status;'
sqlite3 data/kyledurepos.sqlite3 'SELECT COUNT(DISTINCT digest) FROM captures;'
sqlite3 data/kyledurepos.sqlite3 'SELECT COUNT(DISTINCT final_sha256) FROM fetch_jobs WHERE final_sha256 IS NOT NULL;'
```

Start local server:

```bash
caddy fmt --overwrite Caddyfile
caddy validate --config Caddyfile
caddy run --config /home/mojo/projects/archivebackup/Caddyfile
```

Validate local server in another shell:

```bash
curl -I http://127.0.0.1:8080/healthz
curl -I http://127.0.0.1:8080/
curl -I http://127.0.0.1:8080/__definitely_missing_archivebackup_path__
```

Expose via Tailscale:

```bash
sudo tailscale up
tailscale serve reset
tailscale serve --bg --https=443 http://127.0.0.1:8080
tailscale serve status
```

Validate `pwned.ussyco.de` after DNS is configured:

```bash
curl -I https://pwned.ussyco.de/healthz
curl -I https://pwned.ussyco.de/
curl -I https://pwned.ussyco.de/__definitely_missing_archivebackup_path__
```

Resume interrupted recovery:

```bash
. .venv/bin/activate
archive-recovery discover --config configs/kyledurepos.com.toml --kind primary-collapsed
archive-recovery discover --config configs/kyledurepos.com.toml --kind alias-inventory
archive-recovery enqueue --config configs/kyledurepos.com.toml
archive-recovery fetch --config configs/kyledurepos.com.toml
archive-recovery postprocess --config configs/kyledurepos.com.toml
archive-recovery report --config configs/kyledurepos.com.toml
```

## 12. Error Handling Matrix - every relevant HTTP status code and how it's handled

| Status | CDX Handling | Content Fetch Handling |
| --- | --- | --- |
| `000` / network error | Retry with exponential backoff and jitter; persist retry event. | Retry with exponential backoff and jitter; persist `retry_wait`. |
| `200` | Parse JSON page, persist rows and resume key. | Success only if body is non-empty and validation passes; stream bytes, hash, postprocess, dedup. |
| `204` | Treat as empty completion only if no resume key; otherwise failed page. | Mark `failed`; no content to recover. |
| `301` | Unexpected for CDX because client follows redirects; final status is evaluated. | Follow redirects, but final saved content must still come from the `id_` request chain; if final status is non-200, handle final status. |
| `302` | Same as `301`. | Same as `301`. |
| `304` | Not expected; mark failed because conditional requests are not used. | Not expected; mark failed because conditional requests are not used. |
| `400` | Non-retryable; stop query and record error. | Non-retryable; mark failed, optionally try alternate capture later. |
| `401` | Non-retryable; record error. | Non-retryable; mark failed. |
| `403` | Non-retryable by default; record error. | Non-retryable by default; mark failed and try alternate capture only if available. |
| `404` | Non-retryable for that query/page; record error. | Non-retryable for that capture; mark failed and try alternate capture if known. |
| `408` | Retry with backoff. | Retry with backoff. |
| `409` | Non-retryable unless observed transient; record error. | Non-retryable unless observed transient. |
| `410` | Non-retryable; record error. | Non-retryable; mark failed. |
| `413` | Reduce `limit` for CDX if encountered; retry once with `limit=500` as a new query fingerprint. | Non-retryable; mark failed. |
| `414` | Query construction bug; fail fast. | URL construction bug or overlong URL; mark failed. |
| `416` | Non-retryable. | Non-retryable. |
| `418` | Non-retryable unless clearly transient; record error. | Non-retryable unless clearly transient. |
| `421` | Retry with backoff. | Retry with backoff. |
| `425` | Retry with backoff. | Retry with backoff. |
| `429` | Honor `Retry-After`; otherwise CDX backoff starts at 5s, capped at 300s, with jitter; never exceed 1 req/sec. | Honor `Retry-After`; otherwise content backoff starts at 2s, capped at 300s, with jitter; persist `next_attempt_at`. |
| `500` | Retry with backoff. | Retry with backoff. |
| `501` | Non-retryable. | Non-retryable. |
| `502` | Retry with backoff. | Retry with backoff. |
| `503` | Retry with backoff; honor `Retry-After` if present. | Retry with backoff; honor `Retry-After` if present. |
| `504` | Retry with backoff. | Retry with backoff. |
| `507` | Retry once after long backoff; then fail. | Retry once after long backoff; then fail. |
| Other `4xx` | Non-retryable unless explicitly whitelisted. | Non-retryable unless alternate capture selection is useful. |
| Other `5xx` | Retry with backoff up to max attempts. | Retry with backoff up to max attempts. |

Validation failures after HTTP `200`:

| Failure | Handling |
| --- | --- |
| Empty body | Mark `skipped_invalid`; try alternate capture if available. |
| HTML body for expected CSS/JS/binary | Mark `skipped_invalid`; try alternate capture. |
| Known Wayback error page | Mark `skipped_invalid`; try alternate capture. |
| SHA256 duplicate | Mark `skipped_duplicate`; record alias. |
| Path collision with different SHA256 | Append `__u_<hash>` suffix and record collision event. |
| HTML cleanup parse error | Save raw bytes only if MIME is not HTML; for HTML, mark failed and preserve raw object for audit. |

## 13. Estimated Timeline - per-phase time estimates for a typical small personal site archive

| Phase | Estimate |
| --- | ---: |
| Environment setup and config creation | 20-45 minutes |
| Phase 1 CDX primary discovery | 5-30 minutes |
| Phase 1 supplemental alias inventory | 5-45 minutes |
| Phase 2 download pipeline for HTML/assets | 20 minutes-3 hours |
| Phase 3 SHA256 dedup and alias reconciliation | 5-20 minutes |
| Phase 4 post-processing, link rewriting, MIME audit | 15-60 minutes |
| Phase 5 local Caddy serve and validation | 10-20 minutes |
| Phase 6 Tailscale/DNS setup for `pwned.ussyco.de` | 15-60 minutes, depending on tailnet DNS/custom-domain readiness |
| Manual review and alternate-capture retries | 30 minutes-2 hours |

Typical small personal site total: 2-8 hours elapsed, with most time spent waiting on polite Wayback downloads and manual validation of the recovered homepage, top-level pages, CSS, JS, and images.

## 14. Open Questions - decisions that require user input before build starts

1. Should `pwned.ussyco.de` be private tailnet-only via Tailscale Serve, or public internet reachable via Tailscale Funnel?
2. What DNS control is available for `pwned.ussyco.de`: public DNS, split DNS, Tailscale custom-domain support, or only local hosts-file testing?
3. Should recovered active JavaScript be served as-is, or should public exposure be restricted/private because archived scripts may execute third-party requests?
4. Is latest-good composite recovery acceptable, or is a specific historical date range required?
5. Should duplicate final-SHA256 paths required for navigability be emitted as hardlinks, or should duplicates remain manifest-only unless broken links prove a need?
6. Should third-party assets referenced by the site be recovered from Wayback in a later phase, or left as external URLs?
7. Is raw content retention under `raw/sha256/` required long-term for auditability, or can it be pruned after the static site and manifests are validated?
