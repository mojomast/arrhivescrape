from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from archive_recovery.context import RunContext
from archive_recovery.jsonl import append_jsonl


CDX_FIELDS = ("urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length")


@dataclass(frozen=True)
class InventoryResult:
    raw_path: Path
    pages_dir: Path
    page_count: int
    record_count: int
    completed_queries: int


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


def build_query(context: RunContext, host: str, resume_key: str | None = None) -> str:
    opts = cdx_options(context)
    params: list[tuple[str, str]] = [
        ("url", host),
        ("output", "json"),
        ("fl", ",".join(CDX_FIELDS)),
        ("showResumeKey", "true"),
        ("matchType", str(opts.get("match_type", "domain"))),
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
