from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from archive_recovery.context import RunContext
from archive_recovery.jsonl import append_jsonl, read_jsonl
from archive_recovery.pipeline.dependencies import canonical_forms, classify_url, identity_hash
from archive_recovery.pipeline.selection import now_iso


CDX_FIELDS = ("urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length")


@dataclass(frozen=True)
class InventoryResult:
    raw_path: Path
    pages_dir: Path
    page_count: int
    record_count: int
    completed_queries: int


@dataclass(frozen=True)
class DependencyRecoveryResult:
    raw_path: Path
    pages_dir: Path
    report_path: Path
    requests_considered: int
    queries_issued: int
    records_found: int
    records_appended: int


def cdx_options(context: RunContext) -> dict[str, Any]:
    return context.config.raw.get("cdx", {}) if isinstance(context.config.raw.get("cdx"), dict) else {}


def rate_options(context: RunContext) -> dict[str, Any]:
    rate_limits = context.config.raw.get("rate_limits", {})
    if not isinstance(rate_limits, dict):
        return {}
    cdx = rate_limits.get("cdx", {})
    return cdx if isinstance(cdx, dict) else {}


def inventory_hosts(context: RunContext) -> list[str]:
    opts = cdx_options(context)
    hosts = [context.config.domain]
    if opts.get("alias_inventory_enabled", True):
        hosts.extend(context.config.alias_hosts)
    seen: set[str] = set()
    unique: list[str] = []
    for host in hosts:
        clean = host.lower().rstrip(".")
        if clean and clean not in seen:
            unique.append(clean)
            seen.add(clean)
    return unique


def inventory_url(context: RunContext, host: str) -> str:
    prefix = context.config.path_prefix
    return host if prefix == "/" else host + prefix


def build_query(context: RunContext, host: str, resume_key: str | None = None) -> str:
    opts = cdx_options(context)
    params: list[tuple[str, str]] = [
        ("url", inventory_url(context, host)),
        ("output", "json"),
        ("fl", ",".join(CDX_FIELDS)),
        ("showResumeKey", "true"),
        ("matchType", str(opts.get("match_type") or ("prefix" if context.config.path_prefix != "/" else "domain"))),
    ]
    collapse = opts.get("collapse", "digest")
    if collapse:
        params.append(("collapse", str(collapse)))
    limit = opts.get("limit")
    if isinstance(limit, int) and limit > 0:
        params.append(("limit", str(limit)))
    for cdx_filter in opts.get("filters", ["statuscode:200"]):
        params.append(("filter", str(cdx_filter)))
    if resume_key:
        params.append(("resumeKey", resume_key))
    endpoint = str(opts.get("endpoint", "https://web.archive.org/cdx/search/cdx"))
    return endpoint + "?" + urllib.parse.urlencode(params)


def build_dependency_query(context: RunContext, request_url: str, resume_key: str | None = None) -> str:
    opts = cdx_options(context)
    params: list[tuple[str, str]] = [
        ("url", request_url),
        ("output", "json"),
        ("fl", ",".join(CDX_FIELDS)),
        ("showResumeKey", "true"),
        ("matchType", "exact"),
    ]
    collapse = opts.get("collapse", "digest")
    if collapse:
        params.append(("collapse", str(collapse)))
    limit = opts.get("limit")
    if isinstance(limit, int) and limit > 0:
        params.append(("limit", str(limit)))
    for cdx_filter in opts.get("filters", ["statuscode:200"]):
        params.append(("filter", str(cdx_filter)))
    if resume_key:
        params.append(("resumeKey", resume_key))
    endpoint = str(opts.get("endpoint", "https://web.archive.org/cdx/search/cdx"))
    return endpoint + "?" + urllib.parse.urlencode(params)


def parse_cdx_json(payload: bytes) -> tuple[list[dict[str, Any]], str | None]:
    data = json.loads(payload.decode("utf-8"))
    if not isinstance(data, list) or not data:
        return [], None
    header = data[0]
    if not isinstance(header, list):
        return [], None
    records: list[dict[str, Any]] = []
    resume_key: str | None = None
    for row in data[1:]:
        if not isinstance(row, list):
            continue
        if row and row[0] == "resumeKey":
            resume_key = str(row[1]) if len(row) > 1 else None
            continue
        record = {str(header[index]): value for index, value in enumerate(row) if index < len(header)}
        record["original_url"] = record.get("original")
        record["cdx_digest"] = record.get("digest")
        records.append(record)
    return records, resume_key


def fetch(url: str, *, timeout: int = 60) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "archive-recovery-toolkit/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec: user-configured CDX endpoint
        return response.read()


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"completed_hosts": [], "resume_keys": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"completed_hosts": [], "resume_keys": {}}
    return value if isinstance(value, dict) else {"completed_hosts": [], "resume_keys": {}}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_dependency_requests(path: Path, context: RunContext) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    canonical_host = context.config.domain.lower()
    aliases = {h.lower() for h in context.config.alias_hosts}
    by_url: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        url = str(row.get("original_url") or row.get("normalized_url") or "")
        if row.get("scope") != "first-party" or not url:
            continue
        if classify_url(url, canonical_host, aliases) != "first-party":
            continue
        forms = canonical_forms(url, canonical_host, aliases)
        key = identity_hash(forms) or str(row.get("normalized_url") or url)
        current = by_url.get(key)
        if current is None or (row.get("high_value") and not current.get("high_value")):
            by_url[key] = dict(row)
    return sorted(by_url.values(), key=lambda r: (not bool(r.get("high_value")), str(r.get("target_mime_guess") or ""), str(r.get("normalized_url") or r.get("original_url") or "")))


def dependency_query_urls(request_url: str, context: RunContext) -> list[str]:
    canonical_host = context.config.domain.lower()
    aliases = {h.lower() for h in context.config.alias_hosts}
    candidates = [request_url, *sorted(canonical_forms(request_url, canonical_host, aliases))]
    seen: set[str] = set()
    unique: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            unique.append(candidate)
            seen.add(candidate)
    return unique


def inventory_row_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row.get("timestamp") or ""), str(row.get("original_url") or row.get("original") or ""), str(row.get("cdx_digest") or row.get("digest") or ""))


def dependency_record_matches(record: dict[str, Any], request: dict[str, Any], context: RunContext) -> bool:
    canonical_host = context.config.domain.lower()
    aliases = {h.lower() for h in context.config.alias_hosts}
    original = str(record.get("original_url") or record.get("original") or "")
    requested = str(request.get("original_url") or request.get("normalized_url") or "")
    if classify_url(original, canonical_host, aliases) != "first-party":
        return False
    record_forms = canonical_forms(original, canonical_host, aliases)
    request_forms = canonical_forms(requested, canonical_host, aliases)
    return bool(record_forms & request_forms) if record_forms and request_forms else original == requested


def safe_page_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-._")
    return stem[:80] or "dependency"


def next_dependency_page_number(pages_dir: Path, request_id: str, query_index: int) -> int:
    prefix = f"{safe_page_stem(request_id)}-q{query_index:02d}-"
    highest = 0
    for page in pages_dir.glob(f"{prefix}*.json"):
        suffix = page.stem.removeprefix(prefix)
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return highest


def run_inventory(context: RunContext, *, force: bool = False, resume_key: str | None = None) -> InventoryResult:
    context.ensure_dirs()
    raw_path = context.run_dir / "manifests" / "inventory.raw.jsonl"
    pages_dir = context.run_dir / "cdx" / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    state_path = context.run_dir / "ops" / "inventory-state.json"
    if force:
        raw_path.unlink(missing_ok=True)
        state_path.unlink(missing_ok=True)
        for page in pages_dir.glob("*.json"):
            page.unlink()
    state = load_state(state_path)
    completed = set(state.get("completed_hosts", []))
    resume_keys = state.setdefault("resume_keys", {})
    rate = rate_options(context)
    min_interval = float(rate.get("min_interval_seconds", 1.1) or 1.1)
    max_attempts = int(rate.get("max_attempts", 5) or 5)
    base_backoff = float(rate.get("base_backoff_seconds", 5) or 5)
    cap_backoff = float(rate.get("cap_backoff_seconds", 300) or 300)
    timeout = int(rate.get("timeout_seconds", 60) or 60)

    page_count = 0
    record_count = 0
    last_request = 0.0
    for host_index, host in enumerate(inventory_hosts(context), start=1):
        if host in completed and not resume_key:
            continue
        current_resume = resume_key if resume_key and host_index == 1 else resume_keys.get(host)
        page_number = 0
        while True:
            elapsed = time.monotonic() - last_request
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            url = build_query(context, host, current_resume)
            payload: bytes | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    last_request = time.monotonic()
                    payload = fetch(url, timeout=timeout)
                    break
                except (urllib.error.URLError, TimeoutError) as exc:
                    if attempt >= max_attempts:
                        raise RuntimeError(f"CDX request failed for {host}: {exc}") from exc
                    time.sleep(min(base_backoff * attempt, cap_backoff))
            assert payload is not None
            records, next_resume = parse_cdx_json(payload)
            page_number += 1
            page_count += 1
            page_path = pages_dir / f"{host.replace('.', '_')}-{page_number:05d}.json"
            page_path.write_bytes(payload)
            for record in records:
                record["inventory_host"] = host
                record["run_id"] = context.run_id
                append_jsonl(raw_path, record)
            record_count += len(records)
            if not next_resume:
                completed.add(host)
                resume_keys.pop(host, None)
                state["completed_hosts"] = sorted(completed)
                save_state(state_path, state)
                break
            current_resume = next_resume
            resume_keys[host] = next_resume
            save_state(state_path, state)
    return InventoryResult(raw_path, pages_dir, page_count, record_count, len(completed))


def run_dependency_recovery(context: RunContext, *, missing_path: Path | None = None, inventory_path: Path | None = None, report_path: Path | None = None) -> DependencyRecoveryResult:
    context.ensure_dirs()
    missing_path = missing_path or context.run_dir / "manifests" / "missing-dependency-requests.jsonl"
    inventory_path = inventory_path or context.run_dir / "manifests" / "inventory.raw.jsonl"
    report_path = report_path or context.run_dir / "reports" / "dependency-recovery-report.md"
    pages_dir = context.run_dir / "cdx" / "dependency-pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    state_path = context.run_dir / "ops" / "dependency-recovery-state.json"

    requests = load_dependency_requests(missing_path, context)
    existing = {inventory_row_key(row) for row in read_jsonl(inventory_path)} if inventory_path.exists() else set()
    state = load_state(state_path)
    completed = set(state.get("completed_requests", []))
    resume_keys = state.setdefault("resume_keys", {})
    rate = rate_options(context)
    min_interval = float(rate.get("min_interval_seconds", 1.1) or 1.1)
    max_attempts = int(rate.get("max_attempts", 5) or 5)
    base_backoff = float(rate.get("base_backoff_seconds", 5) or 5)
    cap_backoff = float(rate.get("cap_backoff_seconds", 300) or 300)
    timeout = int(rate.get("timeout_seconds", 60) or 60)

    queries = 0
    found = 0
    appended = 0
    skipped = Counter()
    last_request = 0.0
    for request in requests:
        request_id = str(request.get("request_id") or safe_page_stem(str(request.get("normalized_url") or request.get("original_url") or "")))
        if request_id in completed:
            continue
        request_url = str(request.get("original_url") or request.get("normalized_url") or "")
        if not urlsplit(request_url).scheme:
            skipped["invalid_request_url"] += 1
            completed.add(request_id)
            state["completed_requests"] = sorted(completed)
            save_state(state_path, state)
            continue
        query_urls = dependency_query_urls(request_url, context)
        for query_index, query_url in enumerate(query_urls, start=1):
            resume_key_id = request_id if query_index == 1 else f"{request_id}#{query_index}"
            current_resume = resume_keys.get(resume_key_id)
            page_number = next_dependency_page_number(pages_dir, request_id, query_index)
            while True:
                elapsed = time.monotonic() - last_request
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                url = build_dependency_query(context, query_url, current_resume)
                payload: bytes | None = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        last_request = time.monotonic()
                        payload = fetch(url, timeout=timeout)
                        break
                    except (urllib.error.URLError, TimeoutError) as exc:
                        if attempt >= max_attempts:
                            raise RuntimeError(f"CDX dependency request failed for {query_url}: {exc}") from exc
                        time.sleep(min(base_backoff * attempt, cap_backoff))
                assert payload is not None
                queries += 1
                page_number += 1
                page_path = pages_dir / f"{safe_page_stem(request_id)}-q{query_index:02d}-{page_number:05d}.json"
                page_path.write_bytes(payload)
                records, next_resume = parse_cdx_json(payload)
                for record in records:
                    found += 1
                    if not dependency_record_matches(record, request, context):
                        skipped["not_requested_first_party"] += 1
                        continue
                    record["inventory_host"] = urlsplit(record.get("original_url") or record.get("original") or "").hostname or ""
                    record["run_id"] = context.run_id
                    record["dependency_request_id"] = request_id
                    record["dependency_query_url"] = query_url
                    record["dependency_recovery_stage"] = "dependency-recovery"
                    tags = set(record.get("tags") or [])
                    tags.update({"first-party", "dependency-recovery"})
                    record["tags"] = sorted(tags)
                    key = inventory_row_key(record)
                    if key in existing:
                        skipped["duplicate_inventory_row"] += 1
                        continue
                    append_jsonl(inventory_path, record)
                    existing.add(key)
                    appended += 1
                if not next_resume:
                    resume_keys.pop(resume_key_id, None)
                    save_state(state_path, state)
                    break
                current_resume = next_resume
                resume_keys[resume_key_id] = next_resume
                save_state(state_path, state)
        completed.add(request_id)
        state["completed_requests"] = sorted(completed)
        save_state(state_path, state)

    lines = ["# Dependency Recovery Report", "", f"Run ID: `{context.run_id}`", "Status: succeeded", f"Generated: `{now_iso()}`", "", "## Summary", "", f"- Requests considered: {len(requests)}", f"- CDX queries issued: {queries}", f"- CDX records found: {found}", f"- Inventory records appended: {appended}", "", "## Next Step", "", "Rerun `select`, `download`, `dependencies`, `normalize`, and `validate` so recovered dependencies can be selected, fetched, linked locally, and checked.", "", "## Skipped", ""]
    lines.extend(f"- {key}: {value}" for key, value in sorted(skipped.items()))
    if not skipped:
        lines.append("- none")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return DependencyRecoveryResult(inventory_path, pages_dir, report_path, len(requests), queries, found, appended)
