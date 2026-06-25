# Phase 1 Spec: Containerized Wayback Recovery Pipeline

Target recovery domain: `kyledurepos.com`

Served hostname: `pwned.ussyco.de`

Runtime model: Docker Compose services `cdx-crawler`, `downloader`, `deduplicator`, `webserver`, and `tailscale`

Public output model: static files only, served by nginx behind Tailscale Serve/Funnel

Primary constraints:

- CDX discovery must use `collapse=digest`.
- Every content fetch URL must use the Wayback `id_` modifier: `https://web.archive.org/web/{timestamp}id_/{original_url}`.
- CDX API traffic must be serialized at `<= 1 request/second`, with an effective ceiling near `60 requests/minute`.
- CDX and content fetchers must implement exponential backoff for `429` and respect `Retry-After` when present.
- On-disk deduplication must compute SHA256 for saved bytes and deduplicate physical output by SHA256 while keeping all URL aliases in manifests.
- The exposed website must be static output only. No dynamic app server may serve public traffic.
- `pwned.ussyco.de` is served via Tailscale reverse proxy to the nginx container.

## Architecture

```text
                 Internet Archive
        +--------------------------------+
        | CDX API + Wayback replay id_   |
        +---------------+----------------+
                        |
                        | HTTPS, polite rate limits
                        v
+-----------------------+--------------------------+
| Docker Compose network: archivebackup            |
|                                                  |
|  +-------------+     +------------+              |
|  | cdx-crawler | --> | SQLite WAL |              |
|  +------+------+     | state DB   |              |
|         |            +-----+------+              |
|         | CDX rows         | jobs/manifests      |
|         v                  v                     |
|  +-------------+     +------------+              |
|  | downloader  | --> | raw files  |              |
|  +------+------+     +-----+------+              |
|         |                  | SHA256              |
|         v                  v                     |
|  +-------------+     +------------+              |
|  |deduplicator | --> | static site|              |
|  +------+------+     +-----+------+              |
|                                |                 |
|                                v                 |
|                         +------------+           |
|                         | webserver  | nginx     |
|                         +-----+------+           |
|                               | http://webserver:8080
|                               v                 |
|                         +------------+           |
|                         | tailscale  | HTTPS     |
|                         +-----+------+           |
+-------------------------------|------------------+
                                v
                         https://pwned.ussyco.de
```

## Repository Layout

The buildable project layout is:

```text
/home/mojo/projects/archivebackup/
  docker-compose.yml
  Dockerfile.pipeline
  Makefile
  configs/
    nginx.conf
  archive_recovery/
    __init__.py
    cli.py
    cdx.py
    db.py
    dedup.py
    fetch.py
    paths.py
    rewrite.py
  data/
    kyledurepos.sqlite3
  logs/
    recovery.jsonl
  raw/
    sha256/
  recovered/
    kyledurepos.com/
      site/
      manifest.json
      duplicates.json
      selection-report.md
  reports/
    summary.md
  tailscale-state/
```

Only `recovered/kyledurepos.com/site/` is served by nginx. `data`, `logs`, `raw`, `reports`, and manifests remain private operational artifacts.

## Service Responsibilities

`cdx-crawler` discovers successful captures from CDX and writes normalized rows into SQLite. It uses one worker, one HTTP request at a time, `collapse=digest`, `showResumeKey=true`, and sleeps at least one second after every CDX request. It persists resume keys and never starts content downloads.

`downloader` reads selected capture jobs from SQLite and fetches Wayback content using `id_` URLs only. It streams bytes to `raw/sha256/<first-two>/<sha256>`, stores raw SHA256 and byte counts, validates MIME/body consistency, and schedules retries with exponential backoff for `429`, `500`, `502`, `503`, `504`, timeouts, and connection resets.

`deduplicator` converts raw objects into the static mirror tree. It computes final SHA256 after HTML cleanup, removes residual Wayback artifacts from HTML, rewrites internal archive URLs to local static paths, resolves filename collisions, writes `manifest.json` and `duplicates.json`, and keeps one canonical physical output for each final SHA256.

`webserver` is nginx serving only static files from `recovered/kyledurepos.com/site`. It uses deterministic `try_files` rewrites for exact files, directory indexes, and extensionless `.html` paths. Missing files return `404`; there is no SPA fallback.

`tailscale` is a sidecar using the official Tailscale container. It runs `tailscale serve --bg --https=443 http://webserver:8080` so the static nginx site is reachable as HTTPS through Tailscale. If public Funnel exposure is required for `pwned.ussyco.de`, it runs `tailscale funnel --bg --https=443 http://webserver:8080` after Serve is configured.

## CDX Discovery Rules

The CDX query is domain-scoped and paginated:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&collapse=digest&limit=1000&showResumeKey=true
```

Pagination keeps every query parameter identical and only appends `resumeKey`:

```text
https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&collapse=digest&limit=1000&showResumeKey=true&resumeKey=<encoded-resume-key>
```

The implementation must URL-encode the resume key. It must not change `url`, `matchType`, `fl`, `filter`, `collapse`, `limit`, or `showResumeKey` while using a resume key.

CDX rate behavior:

- `CDX_CONCURRENCY=1`.
- `CDX_MIN_INTERVAL_SECONDS=1.1` to stay under the hard `<= 1 req/sec` rule with scheduling overhead.
- Effective ceiling: approximately `54 requests/minute`; this is below the `~60 requests/minute` ceiling.
- On `429`, respect `Retry-After`; otherwise use exponential backoff with jitter.
- Backoff: `min(300, 5 * 2 ** (attempt - 1)) * random(0.5, 1.5)` seconds.
- Max attempts per CDX page: `8`.
- Persist the last successful resume key before continuing.

## Content Fetch Rules

Every content fetch URL must be constructed exactly as:

```text
https://web.archive.org/web/{timestamp}id_/{original_url}
```

Examples:

```text
https://web.archive.org/web/20200101000000id_/https://kyledurepos.com/
https://web.archive.org/web/20200101000000id_/https://kyledurepos.com/assets/site.css
```

Plain Wayback replay URLs are forbidden for automated content downloads:

```text
https://web.archive.org/web/{timestamp}/{original_url}
```

Downloader defaults:

- `CONTENT_CONCURRENCY=4`.
- `CONTENT_TIMEOUT_SECONDS=30`.
- `CONTENT_MAX_ATTEMPTS=5`.
- `CONTENT_BASE_BACKOFF_SECONDS=2`.
- `CONTENT_MAX_BACKOFF_SECONDS=300`.
- Retryable statuses: `429`, `500`, `502`, `503`, `504`.
- Non-retryable statuses: `400`, `401`, `403`, `404`, `410`, unless an alternate capture is selected later.
- Always persist `attempts`, `last_error`, `http_status`, and `next_attempt_at` to SQLite before sleeping or exiting.

## Deduplication Policy

The pipeline has two dedup layers.

CDX layer:

- Use `collapse=digest` in the CDX query to reduce duplicated capture rows before download.
- Store the CDX `digest` with every selected capture.
- Skip enqueueing a second download job for the same CDX digest unless it maps to a higher-priority canonical path or an earlier download failed validation.

On-disk layer:

- Compute SHA256 over raw downloaded bytes.
- Store raw bytes content-addressed at `raw/sha256/<first-two-hex>/<sha256>`.
- Clean/rewrite HTML deterministically.
- Compute final SHA256 over bytes written to the static site tree.
- If a final SHA256 already exists, record the new URL as an alias in `duplicates.json` and `manifest.json` rather than writing a duplicate physical file, unless that duplicate path is required for navigability. If navigability requires it, write a hardlink, not a symlink.

Manifest entry shape:

```json
{
  "original_url": "https://kyledurepos.com/path/?v=1",
  "timestamp": "20200101000000",
  "archive_url": "https://web.archive.org/web/20200101000000id_/https://kyledurepos.com/path/?v=1",
  "statuscode": 200,
  "mimetype": "text/html",
  "cdx_digest": "BASE32DIGEST",
  "raw_sha256": "64_hex_chars",
  "final_sha256": "64_hex_chars",
  "local_path": "path/index.html",
  "duplicate_of": null
}
```

## Static Path Mapping

Canonical host is `kyledurepos.com`. `www.kyledurepos.com` is merged into the same tree after SHA256 validation.

Rules:

- `/` maps to `index.html`.
- `/about` with HTML MIME maps to `about/index.html`.
- `/about/` maps to `about/index.html`.
- `/about/index.html` maps to `about/index.html`.
- Existing asset extensions are preserved: `.css`, `.js`, `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`, `.ico`, `.json`, `.xml`, `.txt`, `.pdf`, `.woff`, `.woff2`, `.ttf`, `.otf`, `.mp4`, `.webm`, `.mp3`, `.wav`.
- Fragments are dropped from download identity and preserved in rewritten links.
- Query strings stay in the manifest. If query-bearing content differs from the no-query variant, append `__q_<8-char-sha256-of-query>` before the extension.
- Unsafe filename characters are replaced with `_`.
- Existing different-content path collisions append `__u_<8-char-sha256-of-normalized-url>` before the extension.

## HTML Cleanup and Rewriting

HTML processing must parse HTML rather than rely on broad regex replacement. It removes only known Wayback artifacts:

- Nodes with `id="wm-ipp"`.
- Wayback toolbar comments `BEGIN WAYBACK TOOLBAR INSERT` through `END WAYBACK TOOLBAR INSERT`.
- Scripts with sources containing `/static/js/ait-client-rewrite.js`, `/static/js/wbhack.js`, `/static/js/playback.js`, or `/static/js/timestamp.js`.
- Stylesheets with hrefs containing `/static/css/banner-styles.css` or `/static/css/iconochive.css`.
- Archive-wrapped internal URLs of the form `/web/<timestamp><modifier>/https://kyledurepos.com/...` or `https://web.archive.org/web/<timestamp><modifier>/https://kyledurepos.com/...`.

Internal links to `kyledurepos.com` and `www.kyledurepos.com` are rewritten to local absolute paths rooted at `/`. External third-party URLs remain external.

## SQLite State

SQLite runs in WAL mode at `data/kyledurepos.sqlite3`.

Required pragmas:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;
```

Required schema:

```sql
CREATE TABLE IF NOT EXISTS cdx_pages (
  id INTEGER PRIMARY KEY,
  query_hash TEXT NOT NULL,
  resume_key TEXT,
  page_number INTEGER NOT NULL,
  status TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  http_status INTEGER,
  error TEXT,
  started_at TEXT,
  finished_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(query_hash, page_number)
);

CREATE TABLE IF NOT EXISTS captures (
  id INTEGER PRIMARY KEY,
  original_url TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  statuscode INTEGER NOT NULL,
  mimetype TEXT,
  digest TEXT NOT NULL,
  length INTEGER,
  source TEXT NOT NULL DEFAULT 'cdx',
  discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(original_url, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_captures_digest ON captures(digest);
CREATE INDEX IF NOT EXISTS idx_captures_original_url ON captures(original_url);

CREATE TABLE IF NOT EXISTS fetch_jobs (
  id INTEGER PRIMARY KEY,
  capture_id INTEGER NOT NULL REFERENCES captures(id) ON DELETE CASCADE,
  original_url TEXT NOT NULL,
  archive_url TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 100,
  status TEXT NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at TEXT,
  last_error TEXT,
  http_status INTEGER,
  raw_path TEXT,
  raw_sha256 TEXT,
  bytes_written INTEGER,
  started_at TEXT,
  finished_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(capture_id)
);

CREATE INDEX IF NOT EXISTS idx_fetch_jobs_due ON fetch_jobs(status, next_attempt_at, priority, id);

CREATE TABLE IF NOT EXISTS outputs (
  id INTEGER PRIMARY KEY,
  fetch_job_id INTEGER NOT NULL REFERENCES fetch_jobs(id) ON DELETE CASCADE,
  original_url TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  mimetype TEXT,
  local_path TEXT NOT NULL,
  final_sha256 TEXT NOT NULL,
  duplicate_of INTEGER REFERENCES outputs(id) ON DELETE SET NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(local_path),
  UNIQUE(final_sha256, local_path)
);

CREATE INDEX IF NOT EXISTS idx_outputs_final_sha256 ON outputs(final_sha256);
```

## Volume Strategy

Use bind mounts for all durable project data so containers can be destroyed and recreated without losing recovery state.

```text
./data:/app/data
```

SQLite WAL database and checkpoint state. Must be writable by pipeline containers.

```text
./logs:/app/logs
```

JSONL logs from all pipeline services.

```text
./raw:/app/raw
```

Content-addressed raw downloads, not served publicly.

```text
./recovered:/app/recovered
```

Static output, manifests, duplicates, and selection reports. nginx receives the site subtree read-only.

```text
./reports:/app/reports
```

Human-readable summaries and validation output.

```text
./tailscale-state:/var/lib/tailscale
```

Persistent Tailscale node state. This avoids a new Tailscale device identity on every container recreation.

## Full docker-compose.yml

```yaml
name: archivebackup

services:
  cdx-crawler:
    build:
      context: .
      dockerfile: Dockerfile.pipeline
    image: archivebackup-pipeline:phase1
    container_name: archivebackup-cdx-crawler
    restart: "no"
    environment:
      SITE_DOMAIN: kyledurepos.com
      SQLITE_PATH: /app/data/kyledurepos.sqlite3
      LOG_PATH: /app/logs/recovery.jsonl
      REPORT_PATH: /app/reports/summary.md
      CDX_URL: https://web.archive.org/cdx
      CDX_MATCH_TYPE: domain
      CDX_OUTPUT: json
      CDX_FIELDS: timestamp,original,mimetype,statuscode,digest,length
      CDX_FILTER: statuscode:200
      CDX_COLLAPSE: digest
      CDX_LIMIT: "1000"
      CDX_SHOW_RESUME_KEY: "true"
      CDX_CONCURRENCY: "1"
      CDX_MIN_INTERVAL_SECONDS: "1.1"
      CDX_MAX_ATTEMPTS: "8"
      CDX_BASE_BACKOFF_SECONDS: "5"
      CDX_MAX_BACKOFF_SECONDS: "300"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./reports:/app/reports
    command: ["python", "-m", "archive_recovery.cli", "discover"]
    networks:
      - archivebackup

  downloader:
    image: archivebackup-pipeline:phase1
    container_name: archivebackup-downloader
    restart: "no"
    depends_on:
      cdx-crawler:
        condition: service_completed_successfully
    environment:
      SITE_DOMAIN: kyledurepos.com
      SQLITE_PATH: /app/data/kyledurepos.sqlite3
      LOG_PATH: /app/logs/recovery.jsonl
      RAW_ROOT: /app/raw
      CONTENT_CONCURRENCY: "4"
      CONTENT_TIMEOUT_SECONDS: "30"
      CONTENT_MAX_ATTEMPTS: "5"
      CONTENT_BASE_BACKOFF_SECONDS: "2"
      CONTENT_MAX_BACKOFF_SECONDS: "300"
      WAYBACK_REPLAY_PREFIX: https://web.archive.org/web
      WAYBACK_REPLAY_MODIFIER: id_
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./raw:/app/raw
      - ./reports:/app/reports
    command: ["python", "-m", "archive_recovery.cli", "download"]
    networks:
      - archivebackup

  deduplicator:
    image: archivebackup-pipeline:phase1
    container_name: archivebackup-deduplicator
    restart: "no"
    depends_on:
      downloader:
        condition: service_completed_successfully
    environment:
      SITE_DOMAIN: kyledurepos.com
      SQLITE_PATH: /app/data/kyledurepos.sqlite3
      LOG_PATH: /app/logs/recovery.jsonl
      RAW_ROOT: /app/raw
      RECOVERED_ROOT: /app/recovered/kyledurepos.com
      SITE_ROOT: /app/recovered/kyledurepos.com/site
      MANIFEST_PATH: /app/recovered/kyledurepos.com/manifest.json
      DUPLICATES_PATH: /app/recovered/kyledurepos.com/duplicates.json
      SELECTION_REPORT_PATH: /app/recovered/kyledurepos.com/selection-report.md
      CANONICAL_HOST: kyledurepos.com
      ALIAS_HOSTS: www.kyledurepos.com
      HARDLINK_DUPLICATES_FOR_NAVIGABILITY: "true"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./raw:/app/raw
      - ./recovered:/app/recovered
      - ./reports:/app/reports
    command: ["python", "-m", "archive_recovery.cli", "deduplicate"]
    networks:
      - archivebackup

  webserver:
    image: nginx:1.27-alpine
    container_name: archivebackup-webserver
    restart: unless-stopped
    depends_on:
      deduplicator:
        condition: service_completed_successfully
    volumes:
      - ./configs/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./recovered/kyledurepos.com/site:/usr/share/nginx/html:ro
    expose:
      - "8080"
    ports:
      - "127.0.0.1:8080:8080"
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://127.0.0.1:8080/ || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    networks:
      - archivebackup

  tailscale:
    image: tailscale/tailscale:v1.68.2
    container_name: archivebackup-tailscale
    restart: unless-stopped
    depends_on:
      webserver:
        condition: service_healthy
    hostname: pwned-ussyco-de
    environment:
      TS_STATE_DIR: /var/lib/tailscale
      TS_USERSPACE: "true"
      TS_HOSTNAME: pwned-ussyco-de
      TS_ACCEPT_DNS: "false"
      TS_EXTRA_ARGS: --advertise-tags=tag:archivebackup
      TS_SERVE_CONFIG: /config/serve.json
    volumes:
      - ./tailscale-state:/var/lib/tailscale
      - ./configs/tailscale-serve.json:/config/serve.json:ro
      - /dev/net/tun:/dev/net/tun
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    command: ["tailscaled", "--state=/var/lib/tailscale/tailscaled.state", "--socket=/tmp/tailscaled.sock"]
    networks:
      - archivebackup

networks:
  archivebackup:
    driver: bridge
```

## Full nginx.conf

```nginx
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    server_tokens off;

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log warn;

    server {
        listen 8080;
        server_name pwned.ussyco.de localhost;

        root /usr/share/nginx/html;
        index index.html index.htm;

        autoindex off;

        add_header X-Content-Type-Options nosniff always;
        add_header Referrer-Policy no-referrer-when-downgrade always;

        location = /healthz {
            access_log off;
            return 200 "ok\n";
        }

        location / {
            try_files $uri $uri/index.html $uri.html =404;
        }
    }
}
```

This serves:

- `/asset.css` as the exact file `/asset.css`.
- `/about/` as `/about/index.html`.
- `/about` as `/about/index.html` first, then `/about.html`.
- Missing files as `404`.

It does not rewrite missing paths to `/index.html`, because the archive is not a single-page app and missing recovered assets must remain visible during validation.

## Tailscale Sidecar Config

The sidecar needs persistent state and one-time authentication. The preferred auth path is an ephemeral or reusable auth key supplied to `make tailscale-up` as `TS_AUTHKEY`. The auth key is not committed to disk.

Create `configs/tailscale-serve.json` with this concrete Serve config:

```json
{
  "TCP": {
    "443": {
      "HTTPS": true
    }
  },
  "Web": {
    "pwned.ussyco.de:443": {
      "Handlers": {
        "/": {
          "Proxy": "http://webserver:8080"
        }
      }
    }
  }
}
```

One-time sidecar startup and private tailnet serving:

```bash
docker compose up -d webserver tailscale
docker compose exec tailscale tailscale up --authkey="$TS_AUTHKEY" --hostname=pwned-ussyco-de --accept-dns=false --advertise-tags=tag:archivebackup
docker compose exec tailscale tailscale serve --bg --https=443 http://webserver:8080
docker compose exec tailscale tailscale serve status
```

Public Funnel exposure for `pwned.ussyco.de`, when the tailnet has Funnel and custom-domain policy enabled:

```bash
docker compose exec tailscale tailscale funnel --bg --https=443 http://webserver:8080
docker compose exec tailscale tailscale funnel status
```

The DNS record for `pwned.ussyco.de` must point to the Tailscale/Funnel hostname or be managed by the tailnet's custom-domain mechanism. For private-only tailnet access, split DNS should map `pwned.ussyco.de` to the sidecar node's Tailscale address.

## Full Makefile

```makefile
SHELL := /bin/sh

COMPOSE := docker compose
SITE := kyledurepos.com
TAILSCALE_HOSTNAME := pwned-ussyco-de
TAILSCALE_TARGET := http://webserver:8080

.PHONY: help init build discover download dedupe recover serve-up serve-down tailscale-up tailscale-serve tailscale-funnel tailscale-status logs status ps validate clean stop down

help:
	@printf '%s\n' 'Targets:'
	@printf '%s\n' '  make init              Create required local directories and config paths'
	@printf '%s\n' '  make build             Build the Python pipeline image'
	@printf '%s\n' '  make discover          Run CDX discovery with collapse=digest'
	@printf '%s\n' '  make download          Fetch Wayback content with id_ URLs only'
	@printf '%s\n' '  make dedupe            Build static site and manifests with SHA256 dedup'
	@printf '%s\n' '  make recover           Run discover, download, and dedupe in order'
	@printf '%s\n' '  make serve-up          Start nginx static webserver'
	@printf '%s\n' '  make tailscale-up      Authenticate/start Tailscale sidecar using TS_AUTHKEY'
	@printf '%s\n' '  make tailscale-serve   Enable private Tailscale Serve HTTPS'
	@printf '%s\n' '  make tailscale-funnel  Enable public Funnel HTTPS when policy allows it'
	@printf '%s\n' '  make validate          Smoke-test nginx static rewrite behavior'
	@printf '%s\n' '  make logs              Follow compose logs'
	@printf '%s\n' '  make down              Stop and remove containers'

init:
	mkdir -p configs data logs raw recovered/$(SITE)/site reports tailscale-state
	test -f configs/nginx.conf
	test -f configs/tailscale-serve.json

build: init
	$(COMPOSE) build cdx-crawler

discover: build
	$(COMPOSE) run --rm cdx-crawler

download: build
	$(COMPOSE) run --rm downloader

dedupe: build
	$(COMPOSE) run --rm deduplicator

recover: discover download dedupe

serve-up: init
	$(COMPOSE) up -d webserver

serve-down:
	$(COMPOSE) stop webserver

tailscale-up: serve-up
	test -n "$$TS_AUTHKEY"
	$(COMPOSE) up -d tailscale
	$(COMPOSE) exec tailscale tailscale up --authkey="$$TS_AUTHKEY" --hostname=$(TAILSCALE_HOSTNAME) --accept-dns=false --advertise-tags=tag:archivebackup

tailscale-serve:
	$(COMPOSE) exec tailscale tailscale serve --bg --https=443 $(TAILSCALE_TARGET)
	$(COMPOSE) exec tailscale tailscale serve status

tailscale-funnel:
	$(COMPOSE) exec tailscale tailscale funnel --bg --https=443 $(TAILSCALE_TARGET)
	$(COMPOSE) exec tailscale tailscale funnel status

tailscale-status:
	$(COMPOSE) exec tailscale tailscale status
	$(COMPOSE) exec tailscale tailscale serve status

validate: serve-up
	curl -fsSI http://127.0.0.1:8080/ >/dev/null
	curl -fsSI http://127.0.0.1:8080/healthz >/dev/null
	if curl -fsSI http://127.0.0.1:8080/__definitely_missing_archivebackup_path__ >/dev/null; then exit 1; else exit 0; fi

logs:
	$(COMPOSE) logs -f --tail=200

status ps:
	$(COMPOSE) ps

stop:
	$(COMPOSE) stop

down:
	$(COMPOSE) down

clean:
	rm -rf data logs raw recovered reports
```

`make clean` intentionally removes recovery outputs and state. It does not remove `tailscale-state`, because deleting Tailscale state creates a new device identity and can leave stale devices in the tailnet admin console.

## Pipeline Image Contract

`Dockerfile.pipeline` must create an image that runs the same CLI module for every pipeline stage. The image contract is:

```text
python -m archive_recovery.cli discover
python -m archive_recovery.cli download
python -m archive_recovery.cli deduplicate
python -m archive_recovery.cli report
```

The Python application must use:

- `httpx.AsyncClient` for HTTP.
- `aiosqlite` or short-lived `sqlite3` connections with WAL mode.
- `beautifulsoup4` plus `lxml` for HTML cleanup.
- `tinycss2` or equivalent parsing for CSS URL extraction if CSS expansion is implemented in Phase 1.
- JSONL logs at `/app/logs/recovery.jsonl`.

The image must not contain secrets. Tailscale auth keys are provided only through environment variables at runtime.

## Buildable Dockerfile.pipeline

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    httpx==0.27.2 \
    aiosqlite==0.20.0 \
    beautifulsoup4==4.12.3 \
    lxml==5.3.0 \
    tinycss2==1.3.0

COPY archive_recovery /app/archive_recovery

RUN mkdir -p /app/data /app/logs /app/raw /app/recovered /app/reports

USER 1000:1000

CMD ["python", "-m", "archive_recovery.cli", "report"]
```

## Operational Runbook

Initial recovery:

```bash
make init
make recover
make serve-up
make validate
TS_AUTHKEY=tskey-auth-xxxxxxxxxxxxxxxxxxxx make tailscale-up
make tailscale-serve
```

Public exposure, only if Funnel and custom-domain policy are enabled:

```bash
make tailscale-funnel
```

Resume interrupted recovery:

```bash
make discover
make download
make dedupe
```

Inspect logs:

```bash
make logs
```

Stop services without deleting state:

```bash
make stop
```

Destroy containers without deleting state:

```bash
make down
```

## Validation Requirements

Before exposing through Tailscale, validate:

- `docker compose ps` shows `webserver` healthy.
- `curl -I http://127.0.0.1:8080/` returns `200` if `index.html` was recovered.
- `curl -I http://127.0.0.1:8080/healthz` returns `200`.
- An intentionally missing path returns `404`.
- `manifest.json` contains one row per selected original URL.
- `duplicates.json` records all SHA256 duplicate aliases.
- No downloaded archive URL in logs omits `id_`.
- CDX logs show no more than one CDX request per second.
- Any `429` event has either a parsed `Retry-After` or an exponential `next_attempt_at`.

After Tailscale Serve:

```bash
docker compose exec tailscale tailscale status
docker compose exec tailscale tailscale serve status
curl -I https://pwned.ussyco.de/
```

For private tailnet deployments, the final `curl` must be run from a tailnet client that resolves `pwned.ussyco.de` to the Tailscale service. For public Funnel deployments, it can be run from the public internet after DNS/custom-domain configuration is active.

## Opinionated Decisions

Use nginx rather than Caddy because this spec requires explicit `try_files` rewrite behavior and an nginx container.

Use Docker Compose for lifecycle because the pipeline has clear stage boundaries and durable volumes. Compose also makes the static server and Tailscale sidecar reproducible.

Use SQLite WAL rather than JSON checkpoints because resumability, retry scheduling, and dedup aliasing need durable indexed state.

Use CDX `collapse=digest` as a network-saving first pass, then SHA256 as the authoritative local dedup layer. CDX digest is useful but not sufficient after cleanup and path normalization.

Use Tailscale as the only HTTPS exposure layer. nginx stays plain HTTP inside the Compose network and on `127.0.0.1:8080` for local validation.

Do not serve manifests, raw downloads, logs, or SQLite through nginx. Only static recovered site files are public.
