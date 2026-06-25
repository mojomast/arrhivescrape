# Minimalist Wayback Recovery Pipeline

This spec defines the Phase 1 minimalist build for recovering `kyledurepos.com` into a static mirror and serving it as `pwned.ussyco.de` through nginx on loopback plus Tailscale Serve HTTPS. It intentionally chooses few moving parts: `waybackpack` for a quick sanity mirror, bash scripts for the auditable pipeline, SQLite for durable state, `curl` for controlled `id_` downloads, nginx for static serving, and Tailscale for HTTPS exposure.

Hard requirements honored here:

- CDX discovery uses `collapse=digest`.
- Every content fetch URL is `https://web.archive.org/web/{timestamp}id_/{original}`.
- CDX API calls are serialized at `<= 1 req/sec`, with a practical ceiling of about `60 req/min`.
- `429`, `500`, `502`, `503`, `504`, timeouts, and transient network failures use exponential backoff.
- Deduplication is two-layer: CDX digest before download, SHA256 after writing bytes to disk.
- Output is static files only.
- Public/private HTTPS exposure target is `pwned.ussyco.de` through Tailscale reverse proxying to local nginx.

## Architecture

```text
                +-----------------------------+
                | Internet Archive CDX API    |
                | collapse=digest, 1 req/sec  |
                +--------------+--------------+
                               |
                               v
                     scripts/discover-cdx.sh
                               |
                               v
       +---------------- data/kyledurepos.sqlite3 ----------------+
       | captures, fetch_jobs, files, aliases, run_events          |
       +-------------------------+---------------------------------+
                                 |
                                 v
                         scripts/fetch.sh
             id_ URLs only, retry/backoff, SHA256 state
                                 |
                                 v
                  recovered/kyledurepos.com/site/
                         static mirror tree only
                                 |
                                 v
                    nginx 127.0.0.1:8080
                                 |
                                 v
           tailscale serve HTTPS -> pwned.ussyco.de

Optional sanity path:
waybackpack -> recovered/waybackpack-smoke/ for visual comparison only.
The authoritative pipeline remains the SQLite/bash/curl path because it enforces id_.
```

## File Tree

```text
/home/mojo/projects/archivebackup/
  spec-minimalist.md
  requirements.txt
  config/
    nginx-pwned.ussyco.de.conf
  data/
    schema.sql
    kyledurepos.sqlite3
  logs/
    cdx.log
    fetch.log
  reports/
    summary.txt
  recovered/
    waybackpack-smoke/
    kyledurepos.com/
      site/
  scripts/
    00-init.sh
    01-waybackpack-smoke.sh
    02-discover-cdx.sh
    03-enqueue.sh
    04-fetch.sh
    05-report.sh
```

## Ordered Build Commands

Run these commands from a blank `/home/mojo/projects/archivebackup` directory on Ubuntu/Debian.

```bash
cd /home/mojo/projects/archivebackup
sudo apt-get update
sudo apt-get install -y bash coreutils curl sqlite3 nginx python3 python3-venv tailscale ca-certificates
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install waybackpack
mkdir -p config data logs reports recovered/waybackpack-smoke recovered/kyledurepos.com/site scripts
```

Create `requirements.txt`:

```bash
printf '%s\n' 'waybackpack' > requirements.txt
```

Create `data/schema.sql`:

```bash
cat > data/schema.sql <<'SQL'
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS captures (
  id INTEGER PRIMARY KEY,
  timestamp TEXT NOT NULL,
  original_url TEXT NOT NULL,
  mimetype TEXT,
  statuscode INTEGER,
  cdx_digest TEXT NOT NULL,
  length INTEGER,
  archive_url TEXT NOT NULL,
  discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(cdx_digest),
  UNIQUE(timestamp, original_url)
);

CREATE TABLE IF NOT EXISTS fetch_jobs (
  id INTEGER PRIMARY KEY,
  capture_id INTEGER NOT NULL REFERENCES captures(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending',
  attempts INTEGER NOT NULL DEFAULT 0,
  next_attempt_at INTEGER NOT NULL DEFAULT 0,
  http_status INTEGER,
  last_error TEXT,
  local_path TEXT,
  sha256 TEXT,
  bytes_written INTEGER,
  started_at TEXT,
  finished_at TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(capture_id)
);

CREATE TABLE IF NOT EXISTS files (
  sha256 TEXT PRIMARY KEY,
  canonical_path TEXT NOT NULL,
  bytes_written INTEGER NOT NULL,
  first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aliases (
  id INTEGER PRIMARY KEY,
  original_url TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  cdx_digest TEXT NOT NULL,
  local_path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  duplicate_of TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS run_events (
  id INTEGER PRIMARY KEY,
  event TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fetch_jobs_due ON fetch_jobs(status, next_attempt_at, id);
CREATE INDEX IF NOT EXISTS idx_captures_original ON captures(original_url);
CREATE INDEX IF NOT EXISTS idx_captures_digest ON captures(cdx_digest);
SQL
```

Create `scripts/00-init.sh`:

```bash
cat > scripts/00-init.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd /home/mojo/projects/archivebackup
mkdir -p config data logs reports recovered/waybackpack-smoke recovered/kyledurepos.com/site scripts
sqlite3 data/kyledurepos.sqlite3 < data/schema.sql
sqlite3 data/kyledurepos.sqlite3 "INSERT INTO run_events(event, detail) VALUES ('init', 'sqlite schema initialized');"
SH
chmod +x scripts/00-init.sh
```

Create `scripts/01-waybackpack-smoke.sh`:

```bash
cat > scripts/01-waybackpack-smoke.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd /home/mojo/projects/archivebackup
. .venv/bin/activate
mkdir -p recovered/waybackpack-smoke logs

# Smoke mirror only. The authoritative fetcher is scripts/04-fetch.sh because it
# constructs every content URL with the required id_ modifier and records SHA256.
waybackpack 'https://kyledurepos.com/' \
  --raw \
  --uniques-only \
  --collapse digest \
  -d recovered/waybackpack-smoke \
  > logs/waybackpack-smoke.log 2>&1 || true
SH
chmod +x scripts/01-waybackpack-smoke.sh
```

Create `scripts/02-discover-cdx.sh`:

```bash
cat > scripts/02-discover-cdx.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd /home/mojo/projects/archivebackup

DB=data/kyledurepos.sqlite3
LOG=logs/cdx.log
mkdir -p logs

cdx_url() {
  local resume="${1:-}"
  local base='https://web.archive.org/cdx?url=kyledurepos.com&matchType=domain&output=json&fl=timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&collapse=digest&limit=1000&showResumeKey=true'
  if [ -n "$resume" ]; then
    printf '%s&resumeKey=%s\n' "$base" "$resume"
  else
    printf '%s\n' "$base"
  fi
}

fetch_page() {
  local url="$1"
  local out="$2"
  local attempt=1
  local max_attempts=6
  local delay=5
  while :; do
    local code
    code=$(curl -L --connect-timeout 20 --max-time 120 -sS -w '%{http_code}' -o "$out" "$url" || printf '000')
    if [ "$code" = "200" ]; then
      printf '%s cdx_ok http=%s url=%s\n' "$(date -Is)" "$code" "$url" >> "$LOG"
      return 0
    fi
    if [ "$attempt" -ge "$max_attempts" ]; then
      printf '%s cdx_failed http=%s attempts=%s url=%s\n' "$(date -Is)" "$code" "$attempt" "$url" >> "$LOG"
      return 1
    fi
    printf '%s cdx_retry http=%s attempt=%s sleep=%s url=%s\n' "$(date -Is)" "$code" "$attempt" "$delay" "$url" >> "$LOG"
    sleep "$delay"
    attempt=$((attempt + 1))
    delay=$((delay * 2))
    if [ "$delay" -gt 300 ]; then delay=300; fi
  done
}

resume=''
page=1
while :; do
  # CDX hard ceiling: one request at a time, at least one second between calls.
  sleep 1
  out="data/cdx-page-${page}.json"
  fetch_page "$(cdx_url "$resume")" "$out"

  python3 - "$out" "$DB" <<'PY'
import json, sqlite3, sys
path, db_path = sys.argv[1], sys.argv[2]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
rows = [r for r in data if isinstance(r, list) and len(r) == 6 and r[0] != 'timestamp']
con = sqlite3.connect(db_path)
con.execute('PRAGMA foreign_keys=ON')
for ts, original, mimetype, statuscode, digest, length in rows:
    archive_url = f'https://web.archive.org/web/{ts}id_/{original}'
    con.execute('''
        INSERT OR IGNORE INTO captures(timestamp, original_url, mimetype, statuscode, cdx_digest, length, archive_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ts, original, mimetype, int(statuscode or 0), digest, int(length or 0), archive_url))
con.execute("INSERT INTO run_events(event, detail) VALUES ('cdx_page_imported', ?)", (f'{path}: {len(rows)} rows',))
con.commit()
con.close()
PY

  resume=$(python3 - "$out" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
key = ''
for item in reversed(data):
    if isinstance(item, str):
        key = item
        break
    if isinstance(item, list) and len(item) == 2 and item[0] == 'resumeKey':
        key = item[1]
        break
print(key)
PY
)
  if [ -z "$resume" ]; then
    break
  fi
  page=$((page + 1))
done
SH
chmod +x scripts/02-discover-cdx.sh
```

Create `scripts/03-enqueue.sh`:

```bash
cat > scripts/03-enqueue.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd /home/mojo/projects/archivebackup
sqlite3 data/kyledurepos.sqlite3 <<'SQL'
INSERT OR IGNORE INTO fetch_jobs(capture_id)
SELECT id FROM captures
WHERE statuscode = 200
  AND cdx_digest IS NOT NULL
  AND cdx_digest != '';
INSERT INTO run_events(event, detail)
VALUES ('enqueue', 'created one fetch job per unique CDX digest capture');
SQL
SH
chmod +x scripts/03-enqueue.sh
```

Create `scripts/04-fetch.sh`:

```bash
cat > scripts/04-fetch.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd /home/mojo/projects/archivebackup

DB=data/kyledurepos.sqlite3
ROOT=recovered/kyledurepos.com/site
LOG=logs/fetch.log
mkdir -p "$ROOT" logs

sqlq() {
  printf "%s" "$1" | sed "s/'/''/g"
}

url_to_path() {
  python3 - "$1" "$2" <<'PY'
import hashlib, os, re, sys
from urllib.parse import urlsplit, unquote
url, mimetype = sys.argv[1], sys.argv[2] or ''
p = urlsplit(url)
path = unquote(p.path or '/')
path = re.sub(r'/+', '/', path)
path = path.lstrip('/')
unsafe = r'[^A-Za-z0-9._/=-]'
path = re.sub(unsafe, '_', path)
if not path or path.endswith('/'):
    path = path + 'index.html'
base = os.path.basename(path)
has_ext = '.' in base
is_html = mimetype.startswith('text/html') or mimetype == ''
if is_html and not has_ext:
    path = path.rstrip('/') + '/index.html'
if p.query:
    qhash = hashlib.sha256(p.query.encode()).hexdigest()[:8]
    root, ext = os.path.splitext(path)
    if ext:
        path = f'{root}__q_{qhash}{ext}'
    else:
        path = f'{path}__q_{qhash}'
print(path)
PY
}

due_job() {
  sqlite3 -separator $'\t' "$DB" "
    SELECT j.id, c.id, c.archive_url, c.original_url, c.timestamp, c.mimetype, c.cdx_digest
    FROM fetch_jobs j JOIN captures c ON c.id = j.capture_id
    WHERE j.status IN ('pending', 'retry_wait')
      AND j.next_attempt_at <= strftime('%s','now')
      AND j.attempts < 6
    ORDER BY j.id
    LIMIT 1;"
}

while row=$(due_job); [ -n "$row" ]; do
  IFS=$'\t' read -r job_id capture_id archive_url original_url timestamp mimetype cdx_digest <<< "$row"
  rel=$(url_to_path "$original_url" "$mimetype")
  final="$ROOT/$rel"
  tmp="${final}.part"
  mkdir -p "$(dirname "$final")"
  original_sql=$(sqlq "$original_url")
  timestamp_sql=$(sqlq "$timestamp")
  digest_sql=$(sqlq "$cdx_digest")

  sqlite3 "$DB" "UPDATE fetch_jobs SET status='in_progress', attempts=attempts+1, started_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=$job_id;"
  attempt=$(sqlite3 "$DB" "SELECT attempts FROM fetch_jobs WHERE id=$job_id;")

  code=$(curl -L --connect-timeout 20 --max-time 180 -sS -w '%{http_code}' -o "$tmp" "$archive_url" || printf '000')
  bytes=0
  [ -f "$tmp" ] && bytes=$(wc -c < "$tmp" | tr -d ' ')

  if [ "$code" = "200" ] && [ "$bytes" -gt 0 ]; then
    sha=$(sha256sum "$tmp" | cut -d ' ' -f 1)
    existing=$(sqlite3 "$DB" "SELECT canonical_path FROM files WHERE sha256='$sha' LIMIT 1;")
    if [ -n "$existing" ]; then
      rel_sql=$(sqlq "$rel")
      existing_sql=$(sqlq "$existing")
      rm -f "$tmp"
      sqlite3 "$DB" "
        UPDATE fetch_jobs SET status='succeeded', http_status=$code, local_path='$rel_sql', sha256='$sha', bytes_written=$bytes, finished_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=$job_id;
        INSERT INTO aliases(original_url, timestamp, cdx_digest, local_path, sha256, duplicate_of) VALUES ('$original_sql', '$timestamp_sql', '$digest_sql', '$rel_sql', '$sha', '$existing_sql');"
      printf '%s duplicate job=%s sha=%s rel=%s duplicate_of=%s\n' "$(date -Is)" "$job_id" "$sha" "$rel" "$existing" >> "$LOG"
    else
      if [ -e "$final" ]; then
        suffix=$(printf '%s' "$original_url" | sha256sum | cut -d ' ' -f 1 | cut -c 1-8)
        dir=$(dirname "$rel")
        name=$(basename "$rel")
        stem=${name%.*}
        ext=${name##*.}
        if [ "$stem" = "$ext" ]; then
          rel="$dir/${name}__$suffix"
        else
          rel="$dir/${stem}__$suffix.${ext}"
        fi
        final="$ROOT/$rel"
        mkdir -p "$(dirname "$final")"
      fi
      rel_sql=$(sqlq "$rel")
      mv "$tmp" "$final"
      sqlite3 "$DB" "
        INSERT INTO files(sha256, canonical_path, bytes_written) VALUES ('$sha', '$rel_sql', $bytes);
        UPDATE fetch_jobs SET status='succeeded', http_status=$code, local_path='$rel_sql', sha256='$sha', bytes_written=$bytes, finished_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE id=$job_id;
        INSERT INTO aliases(original_url, timestamp, cdx_digest, local_path, sha256, duplicate_of) VALUES ('$original_sql', '$timestamp_sql', '$digest_sql', '$rel_sql', '$sha', NULL);"
      printf '%s fetched job=%s http=%s bytes=%s sha=%s rel=%s\n' "$(date -Is)" "$job_id" "$code" "$bytes" "$sha" "$rel" >> "$LOG"
    fi
  else
    rm -f "$tmp"
    if [ "$code" = "429" ] || [ "$code" = "500" ] || [ "$code" = "502" ] || [ "$code" = "503" ] || [ "$code" = "504" ] || [ "$code" = "000" ]; then
      delay=$((5 * (2 ** (attempt - 1))))
      if [ "$delay" -gt 300 ]; then delay=300; fi
      next=$(( $(date +%s) + delay ))
      sqlite3 "$DB" "UPDATE fetch_jobs SET status='retry_wait', http_status=$code, last_error='retryable http $code', next_attempt_at=$next, updated_at=CURRENT_TIMESTAMP WHERE id=$job_id;"
      printf '%s retry job=%s http=%s attempt=%s sleep=%s url=%s\n' "$(date -Is)" "$job_id" "$code" "$attempt" "$delay" "$archive_url" >> "$LOG"
    else
      sqlite3 "$DB" "UPDATE fetch_jobs SET status='failed', http_status=$code, last_error='non-retryable or empty response', updated_at=CURRENT_TIMESTAMP WHERE id=$job_id;"
      printf '%s failed job=%s http=%s bytes=%s url=%s\n' "$(date -Is)" "$job_id" "$code" "$bytes" "$archive_url" >> "$LOG"
    fi
  fi
done
SH
chmod +x scripts/04-fetch.sh
```

Create `scripts/05-report.sh`:

```bash
cat > scripts/05-report.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cd /home/mojo/projects/archivebackup
{
  printf 'Minimalist recovery summary\n'
  printf 'Generated: %s\n\n' "$(date -Is)"
  printf 'Fetch jobs by status:\n'
  sqlite3 data/kyledurepos.sqlite3 "SELECT status || ': ' || COUNT(*) FROM fetch_jobs GROUP BY status ORDER BY status;"
  printf '\nHTTP statuses:\n'
  sqlite3 data/kyledurepos.sqlite3 "SELECT COALESCE(http_status, 0) || ': ' || COUNT(*) FROM fetch_jobs GROUP BY http_status ORDER BY COUNT(*) DESC;"
  printf '\nCounts:\n'
  sqlite3 data/kyledurepos.sqlite3 "SELECT 'captures: ' || COUNT(*) FROM captures;"
  sqlite3 data/kyledurepos.sqlite3 "SELECT 'unique sha256 files: ' || COUNT(*) FROM files;"
  sqlite3 data/kyledurepos.sqlite3 "SELECT 'aliases: ' || COUNT(*) FROM aliases;"
} > reports/summary.txt
cat reports/summary.txt
SH
chmod +x scripts/05-report.sh
```

Run the recovery in this order:

```bash
./scripts/00-init.sh
./scripts/01-waybackpack-smoke.sh
./scripts/02-discover-cdx.sh
./scripts/03-enqueue.sh
./scripts/04-fetch.sh
./scripts/05-report.sh
```

## Full nginx Config

Create `config/nginx-pwned.ussyco.de.conf`:

```bash
cat > config/nginx-pwned.ussyco.de.conf <<'NGINX'
server {
    listen 127.0.0.1:8080;
    server_name pwned.ussyco.de localhost;

    root /home/mojo/projects/archivebackup/recovered/kyledurepos.com/site;
    index index.html index.htm;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    autoindex off;
    sendfile on;
    tcp_nopush on;

    add_header X-Content-Type-Options nosniff always;

    location / {
        try_files $uri $uri/index.html $uri.html =404;
    }

    location ~ /\. {
        return 404;
    }
}
NGINX
```

Install and start nginx with the config:

```bash
sudo cp config/nginx-pwned.ussyco.de.conf /etc/nginx/conf.d/pwned.ussyco.de.conf
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
curl -I http://127.0.0.1:8080/
```

Expose through Tailscale Serve HTTPS:

```bash
sudo tailscale up
tailscale serve reset
tailscale serve --bg --https=443 http://127.0.0.1:8080
tailscale serve status
```

If the tailnet has custom-domain support for `pwned.ussyco.de`, map that name to this node in the Tailscale admin/DNS configuration. If public internet exposure is required and Funnel is explicitly enabled for the tailnet, use this instead of private Serve:

```bash
tailscale serve reset
tailscale funnel --bg --https=443 http://127.0.0.1:8080
tailscale funnel status
```

## Dedup Strategy

Discovery deduplication is performed by the CDX query itself with `collapse=digest`. SQLite also enforces `UNIQUE(cdx_digest)`, so a rerun or a resumed CDX traversal cannot enqueue repeated digest-equivalent captures.

Fetch deduplication is performed after download by computing SHA256 over the exact bytes written by the `id_` response. The first file for a SHA256 becomes the canonical physical file in `recovered/kyledurepos.com/site`. Later responses with the same SHA256 are not written again; they are recorded in `aliases` with `duplicate_of` pointing at the canonical path.

Path collision handling is deterministic. URL paths are normalized into a static mirror tree, query strings become `__q_<8-char-sha256(query)>` suffixes, HTML routes without extensions become `index.html`, and true path collisions append an 8-character SHA256 suffix derived from the full original URL.

This keeps setup fast and storage small while preserving auditability in SQLite. The served output remains plain static files; SQLite is state and manifest only, never a runtime dependency for nginx.

## Error Handling

CDX errors:

- CDX requests are strictly sequential.
- Each CDX request sleeps at least one second before execution.
- `429`, `500`, `502`, `503`, `504`, `000`, timeouts, and curl failures retry up to six attempts.
- Backoff starts at five seconds and doubles to a maximum of 300 seconds.
- Successful and failed CDX pages are logged to `logs/cdx.log`.

Content fetch errors:

- Content fetches use only the stored `archive_url`, always with `id_`.
- `200` with non-empty body is success.
- `429`, `500`, `502`, `503`, `504`, and `000` are retryable.
- Retry delay is exponential: `5 * 2^(attempt-1)` seconds, capped at 300 seconds.
- Retry state is persisted in SQLite as `retry_wait` with `next_attempt_at`, so interruption does not lose backoff state.
- Other HTTP statuses and empty responses are marked `failed` for later review.
- No failed download overwrites an existing file because bytes are written to `.part` files and moved into place only after validation and SHA256 calculation.

Resume behavior:

- Re-run `02-discover-cdx.sh` safely; inserts are idempotent.
- Re-run `03-enqueue.sh` safely; jobs are unique per capture.
- Re-run `04-fetch.sh` safely; it only claims `pending` and due `retry_wait` jobs.
- Existing successful jobs are not refetched unless manually reset in SQLite.

Validation commands:

```bash
sqlite3 data/kyledurepos.sqlite3 "SELECT status, COUNT(*) FROM fetch_jobs GROUP BY status;"
sqlite3 data/kyledurepos.sqlite3 "SELECT COUNT(*) FROM files;"
sqlite3 data/kyledurepos.sqlite3 "SELECT COUNT(*) FROM aliases WHERE duplicate_of IS NOT NULL;"
curl -I http://127.0.0.1:8080/
curl -I http://127.0.0.1:8080/missing-file
tailscale serve status
```

Expected hosting behavior:

- Exact assets are served as-is.
- `/about` resolves to `/about/index.html` or `/about.html` if present.
- Missing files return `404`.
- Directory browsing is disabled.
- HTTPS is handled by Tailscale, not nginx.
