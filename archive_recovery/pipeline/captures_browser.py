from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from archive_recovery.context import RunContext
from archive_recovery.jsonl import read_jsonl
from archive_recovery.pipeline.selection import now_iso


@dataclass(frozen=True)
class CaptureBrowserResult:
    html_path: Path
    json_path: Path
    groups: int
    captures: int


def archive_id_url(timestamp: str, original_url: str) -> str:
    return f"https://web.archive.org/web/{timestamp}id_/{original_url}"


def group_key(url: str) -> str:
    parts = urlsplit(url)
    return f"{(parts.hostname or '').lower().removeprefix('www.')}{parts.path or '/'}"


def run_captures_browser(context: RunContext, *, inventory_path: Path | None = None, selection_path: Path | None = None, site_manifest_path: Path | None = None, output_dir: Path | None = None) -> CaptureBrowserResult:
    context.ensure_dirs()
    inventory_path = inventory_path or context.run_dir / "manifests" / "inventory.raw.jsonl"
    selection_path = selection_path or context.run_dir / "manifests" / "selection.pruned.jsonl"
    site_manifest_path = site_manifest_path or context.run_dir / "manifests" / "site.manifest.jsonl"
    output_dir = output_dir or context.run_dir / "reports" / "captures-browser"
    output_dir.mkdir(parents=True, exist_ok=True)
    local_by_url = {}
    if selection_path.exists():
        for row in read_jsonl(selection_path):
            if row.get("selected_original_url"):
                local_by_url[(row.get("selected_timestamp"), row.get("selected_original_url"))] = {"selected": True, "local_path": row.get("output_path_hint")}
    if site_manifest_path.exists():
        for row in read_jsonl(site_manifest_path):
            if row.get("source_url"):
                local_by_url[(row.get("timestamp"), row.get("source_url"))] = {"selected": True, "local_path": row.get("output_path")}
    groups: dict[str, dict] = defaultdict(lambda: {"captures": [], "mime_classes": Counter(), "selected": 0})
    total = 0
    for row in read_jsonl(inventory_path):
        original = row.get("original_url") or row.get("original") or ""
        timestamp = row.get("timestamp") or ""
        key = group_key(original)
        local = local_by_url.get((timestamp, original), {})
        capture = {"timestamp": timestamp, "original_url": original, "archive_url": row.get("archive_url") or archive_id_url(timestamp, original), "mimetype": row.get("mimetype") or "", "statuscode": row.get("statuscode"), "selected": bool(local), "local_path": local.get("local_path")}
        groups[key]["captures"].append(capture)
        groups[key]["mime_classes"][capture["mimetype"] or "unknown"] += 1
        groups[key]["selected"] += int(bool(local)); total += 1
    serializable = {key: {"captures": value["captures"], "mime_classes": dict(value["mime_classes"]), "selected": value["selected"]} for key, value in sorted(groups.items())}
    json_path = output_dir / "captures.json"
    json_path.write_text(json.dumps({"run_id": context.run_id, "generated_at": now_iso(), "groups": serializable}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = []
    for key, value in serializable.items():
        rows.append(f"<h2>{html.escape(key)}</h2><p>{len(value['captures'])} captures, {value['selected']} local/selected</p><ul>")
        for cap in value["captures"][:200]:
            local = f" — local: <code>{html.escape(cap['local_path'] or '')}</code>" if cap.get("local_path") else ""
            rows.append(f"<li><a href=\"{html.escape(cap['archive_url'], quote=True)}\">{html.escape(cap['timestamp'])}</a> {html.escape(cap['mimetype'])}{local}</li>")
        rows.append("</ul>")
    html_path = output_dir / "index.html"
    html_path.write_text("<!doctype html><meta charset='utf-8'><title>Capture Browser</title><style>body{font-family:sans-serif;max-width:1100px;margin:2rem auto}code{background:#eee;padding:.1rem .25rem}</style>" + f"<h1>Capture Browser: {html.escape(context.run_id)}</h1><p>{len(groups)} URL groups, {total} captures. Data: <a href='captures.json'>captures.json</a></p>" + "\n".join(rows), encoding="utf-8")
    return CaptureBrowserResult(html_path, json_path, len(groups), total)
