from __future__ import annotations

import hashlib
import os
import random
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from archive_recovery.context import RunContext
from archive_recovery.jsonl import read_jsonl, write_jsonl


HTML_REJECT_CLASSES = {"css", "javascript", "image", "font", "pdf", "audio", "video"}
WAYBACK_ERROR_PATTERNS = (
    b"wayback machine doesn't have that page archived",
    b"the wayback machine has not archived",
    b"this url has been excluded from the wayback machine",
    b"page cannot be displayed due to robots.txt",
    b"not available on web.archive.org",
    b"got an http 302 response at crawl time",
    b"hrm. the wayback machine has not archived",
)
RETRY_STATUSES = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class DownloadResult:
    results_path: Path
    report_path: Path
    attempted: int
    succeeded: int
    failed: int
    skipped: int


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return max(0.0, float(value))
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())


def retry_delay(response_headers: dict[str, str] | None, attempt: int, *, base: float, cap: float) -> tuple[float, str]:
    retry_after = parse_retry_after((response_headers or {}).get("Retry-After"))
    if retry_after is not None:
        return retry_after, "retry_after"
    return min(cap, base * (2 ** max(0, attempt - 1))) * random.uniform(0.5, 1.5), "exponential_backoff"


def archive_url(row: dict) -> str:
    return f"https://web.archive.org/web/{row['selected_timestamp']}id_/{row['selected_original_url']}"


def is_html_body(prefix: bytes) -> bool:
    sample = prefix[:1024].lstrip().lower()
    return sample.startswith(b"<!doctype html") or sample.startswith(b"<html") or b"<html" in sample[:256]


def has_wayback_error_signature(prefix: bytes) -> bool:
    sample = prefix[:65536].lower()
    return any(pattern in sample for pattern in WAYBACK_ERROR_PATTERNS)


def classify_validation(row: dict, status: int | None, content_type: str | None, byte_count: int, prefix: bytes) -> tuple[str, str | None]:
    if status != 200:
        return "http_error", f"http_status_{status}"
    if byte_count <= 0:
        return "skipped_invalid", "empty_body"
    if has_wayback_error_signature(prefix):
        return "skipped_invalid", "wayback_error_page_signature"
    expected_class = row.get("mime_class") or "unknown"
    content_type_base = (content_type or "").split(";", 1)[0].strip().lower()
    looks_html = content_type_base in {"text/html", "application/xhtml+xml"} or is_html_body(prefix)
    if expected_class in HTML_REJECT_CLASSES and looks_html:
        return "skipped_invalid", f"html_body_for_expected_{expected_class}"
    return "valid", None


def content_settings(context: RunContext) -> tuple[int, int, int, float, float]:
    rate = context.config.raw.get("rate_limits", {}).get("content", {}) if isinstance(context.config.raw.get("rate_limits"), dict) else {}
    workers = int(rate.get("workers", 4) or 4)
    timeout = int(rate.get("timeout_seconds", 30) or 30)
    max_attempts = int(rate.get("max_attempts", 8) or 8)
    base = float(rate.get("base_backoff_seconds", 5) or 5)
    cap = float(rate.get("cap_backoff_seconds", 300) or 300)
    return max(1, workers), timeout, max(1, max_attempts), base, cap


def fetch_once(url: str, timeout: int, user_agent: str) -> tuple[int | None, str | None, str | None, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.geturl(), response.headers.get("Content-Type"), dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.geturl(), exc.headers.get("Content-Type"), dict(exc.headers.items()), exc.read()


def store_raw(raw_root: Path, data: bytes) -> tuple[str, str]:
    digest = hashlib.sha256(data).hexdigest()
    dest = raw_root / digest[:2] / digest
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        part = dest.with_name(f"{dest.name}.{os.getpid()}.{threading.get_ident()}.part")
        part.write_bytes(data)
        try:
            os.replace(part, dest)
        except FileExistsError:
            part.unlink(missing_ok=True)
    return digest, str(dest)


def download_one(context: RunContext, row: dict, index: int, *, timeout: int, max_attempts: int, base: float, cap: float, user_agent: str) -> dict:
    started = now_iso()
    job_id = row.get("selection_id") or f"download-{index:05d}"
    url = archive_url(row)
    status = None; final_url = None; content_type = None; bytes_downloaded = 0
    raw_sha256 = None; raw_path = None; attempts = 0; error = None
    fetch_state = "failed"; validation_state = "not_validated"
    tags = list(row.get("tags") or [])
    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        headers: dict[str, str] = {}
        try:
            status, final_url, content_type, headers, data = fetch_once(url, timeout, user_agent)
            bytes_downloaded = len(data)
            validation_state, error = classify_validation(row, status, content_type, bytes_downloaded, data[:65536])
            if validation_state == "valid":
                raw_sha256, raw_path = store_raw(context.config.raw_root, data)
                fetch_state = "succeeded"; tags.append("downloaded")
                break
            if validation_state == "skipped_invalid":
                fetch_state = "skipped"; tags.append("skipped_invalid")
                break
            if status not in RETRY_STATUSES or attempt == max_attempts:
                fetch_state = "failed"
                break
        except (OSError, TimeoutError, urllib.error.URLError) as exc:
            error = type(exc).__name__
            validation_state = "network_error"
            if attempt == max_attempts:
                fetch_state = "failed"
                break
        delay, _reason = retry_delay(headers, attempt, base=base, cap=cap)
        time.sleep(delay)
    return {"run_id": context.run_id, "job_id": job_id, "original_url": row.get("selected_original_url"), "archive_url": url, "requested_timestamp": row.get("selected_timestamp"), "http_status": status, "final_fetch_url": final_url, "response_content_type": content_type, "bytes_downloaded": bytes_downloaded, "raw_sha256": raw_sha256, "raw_path": raw_path, "attempts": attempts, "started_at": started, "finished_at": now_iso(), "fetch_state": fetch_state, "validation_state": validation_state, "error": error, "tags": tags}


def report(context: RunContext, results: list[dict]) -> str:
    counts = Counter(r["fetch_state"] for r in results)
    validations = Counter(r["validation_state"] for r in results)
    errors = Counter(r["error"] for r in results if r.get("error"))
    lines = ["# Download Report", "", f"Run ID: `{context.run_id}`", "Status: succeeded", f"Generated: `{now_iso()}`", "", "## Summary", "", f"- Attempted: {len(results)}", f"- Succeeded: {counts['succeeded']}", f"- Failed: {counts['failed']}", f"- Skipped: {counts['skipped']}", f"- Unique raw objects: {len({r['raw_sha256'] for r in results if r.get('raw_sha256')})}", "", "## Validation States", ""]
    lines.extend(f"- {key}: {value}" for key, value in sorted(validations.items()))
    lines.extend(["", "## Top Errors", ""])
    lines.extend([f"- {key}: {value}" for key, value in errors.most_common(20)] or ["- none"])
    return "\n".join(lines) + "\n"


def run_download(context: RunContext, *, selection_path: Path | None = None, results_path: Path | None = None, report_path: Path | None = None) -> DownloadResult:
    context.ensure_dirs()
    selection_path = selection_path or context.run_dir / "manifests" / "selection.pruned.jsonl"
    results_path = results_path or context.run_dir / "manifests" / "download.results.jsonl"
    report_path = report_path or context.run_dir / "reports" / "download-report.md"
    rows = list(read_jsonl(selection_path))
    workers, timeout, max_attempts, base, cap = content_settings(context)
    user_agent = f"archive-recovery/{context.run_id}"
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(download_one, context, row, i, timeout=timeout, max_attempts=max_attempts, base=base, cap=cap, user_agent=user_agent) for i, row in enumerate(rows)]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: r["job_id"])
    write_jsonl(results_path, results)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report(context, results), encoding="utf-8")
    counts = Counter(r["fetch_state"] for r in results)
    return DownloadResult(results_path, report_path, len(results), counts["succeeded"], counts["failed"], counts["skipped"])
