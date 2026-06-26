from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from archive_recovery.context import RunContext
from archive_recovery.jsonl import write_jsonl


UNRESERVED = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
HIGH_VALUE_PREFIXES = ("/", "/about", "/archives", "/blog", "/contact", "/feed", "/index", "/portfolio", "/projects", "/resume", "/rss", "/sitemap", "/wp-content/")
INDEX_RE = re.compile(r"/(?:index|default)\.(?:html?|php|asp|aspx)$", re.IGNORECASE)
EXT_CLASS = {".html": "html", ".htm": "html", ".php": "html", ".asp": "html", ".aspx": "html", ".css": "css", ".js": "javascript", ".mjs": "javascript", ".jpg": "image", ".jpeg": "image", ".png": "image", ".gif": "image", ".webp": "image", ".svg": "image", ".ico": "image", ".woff": "font", ".woff2": "font", ".ttf": "font", ".otf": "font", ".eot": "font", ".pdf": "pdf", ".json": "json", ".xml": "xml", ".rss": "xml", ".txt": "text"}


@dataclass(frozen=True)
class SelectionResult:
    selection_path: Path
    canonical_path: Path
    report_path: Path
    raw_rows: int
    selected: int
    canonical_records: int


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def decode_unreserved(path: str) -> str:
    def repl(match: re.Match[str]) -> str:
        char = bytes.fromhex(match.group(1)).decode("latin-1")
        return char if char in UNRESERVED else match.group(0).upper()
    return re.sub(r"%([0-9A-Fa-f]{2})", repl, path)


def normalize_path(path: str) -> str:
    path = path or "/"
    path = re.sub(r"/{2,}", "/", path)
    if not path.startswith("/"):
        path = "/" + path
    return decode_unreserved(path)


def mime_class(mimetype: str | None) -> str:
    mt = (mimetype or "").split(";", 1)[0].strip().lower()
    if mt in ("text/html", "application/xhtml+xml"):
        return "html"
    if mt == "text/css":
        return "css"
    if mt in ("application/javascript", "application/x-javascript", "text/javascript"):
        return "javascript"
    if mt.startswith("image/"):
        return "image"
    if mt.startswith("font/") or mt in ("application/font-woff", "application/x-font-ttf", "application/vnd.ms-fontobject"):
        return "font"
    if mt == "application/pdf":
        return "pdf"
    if mt.startswith("audio/"):
        return "audio"
    if mt.startswith("video/"):
        return "video"
    if mt in ("application/json", "text/json") or mt.endswith("+json"):
        return "json"
    if mt in ("application/xml", "text/xml", "application/rss+xml", "application/atom+xml") or mt.endswith("+xml"):
        return "xml"
    if mt.startswith("text/"):
        return "text"
    return "unknown"


def ext_class(path: str) -> str | None:
    return EXT_CLASS.get(Path(urlsplit("http://x" + path).path).suffix.lower())


def route_class(path: str, query: str, cls: str) -> str:
    if path == "/" or INDEX_RE.search(path):
        return "homepage"
    if query:
        return "query_variant"
    if cls == "html" and (not Path(path.lower()).suffix or INDEX_RE.search(path)):
        return "html_route"
    return cls if cls != "unknown" else "unknown"


def output_path_hint(path: str, query: str, cls: str) -> str:
    path = INDEX_RE.sub("/", path)
    if cls == "html" and (path == "/" or not Path(path).suffix or path.endswith("/")):
        out = "index.html" if not path.strip("/") else f"{path.strip('/')}/index.html"
    else:
        out = path.lstrip("/") or "index.html"
    if query:
        qhash = sha256_text(query)[:8]
        p = Path(out)
        out = str(p.with_name(f"{p.stem}__q_{qhash}{p.suffix}")) if p.suffix else f"{out}__q_{qhash}"
    return out.replace("//", "/")


def normalize_url(original_url: str, canonical_host: str, alias_hosts: set[str], mimetype: str | None) -> tuple[str, str, bool, str, str]:
    parts = urlsplit(original_url)
    scheme = (parts.scheme or "http").lower()
    host = (parts.hostname or "").lower().rstrip(".")
    folded_www = False
    if host in alias_hosts or host == "www." + canonical_host:
        host = canonical_host
        folded_www = True
    path = normalize_path(parts.path)
    cls = mime_class(mimetype)
    if cls == "html":
        path = INDEX_RE.sub("/", path)
        if not Path(path).suffix and not path.endswith("/"):
            path += "/"
    normalized = urlunsplit((scheme, host, path, parts.query, ""))
    identity_url = urlunsplit(("https", canonical_host if host == canonical_host else host, path, parts.query, ""))
    return normalized, identity_url, folded_www, path, parts.query


def to_int(value: object) -> int | None:
    if value in (None, "", "-"):
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def load_rows(path: Path, context: RunContext) -> tuple[list[dict], int]:
    rows: list[dict] = []
    parse_errors = 0
    canonical_host = context.config.domain.lower()
    alias_hosts = {h.lower() for h in context.config.alias_hosts}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            if not isinstance(row, dict):
                parse_errors += 1
                continue
            row["raw_line_number"] = line_number
            row["statuscode"] = to_int(row.get("statuscode"))
            row["length"] = to_int(row.get("length"))
            original = str(row.get("original_url") or row.get("original") or "")
            row["original_url"] = original
            row["cdx_digest"] = row.get("cdx_digest") or row.get("digest")
            normalized_url, identity_url, folded_www, path_value, query = normalize_url(original, canonical_host, alias_hosts, row.get("mimetype"))
            row.update({"normalized_url": normalized_url, "url_identity": sha256_text(identity_url), "identity_url": identity_url, "www_folded": folded_www, "path": path_value, "query": query, "mime_class": mime_class(row.get("mimetype")), "extension_class": ext_class(path_value)})
            row["route_class"] = route_class(path_value, query, row["mime_class"])
            row["output_path_hint"] = output_path_hint(path_value, query, row["mime_class"])
            rows.append(row)
    return rows, parse_errors


def expected_classes(context: RunContext) -> set[str]:
    content = context.config.raw.get("content", {})
    if isinstance(content, dict) and isinstance(content.get("expected_mime_classes"), list):
        return {str(item) for item in content["expected_mime_classes"]}
    return {"html", "css", "javascript", "image", "font", "pdf", "audio", "video", "text", "json", "xml"}


def score_record(row: dict, canonical_host: str, expected: set[str]) -> tuple[float, list[str]]:
    host = (urlsplit(row["original_url"]).hostname or "").lower().rstrip(".")
    score = 0.0
    reasons: list[str] = []
    if row.get("statuscode") == 200:
        score += 500; reasons.append("status-200")
    if row["mime_class"] in expected:
        score += 120; reasons.append(f"expected-{row['mime_class']}")
    else:
        score -= 80; reasons.append("unexpected-mime")
    length = row.get("length")
    if isinstance(length, int) and length > 0:
        score += min(100, int(length ** 0.5)); reasons.append("non-empty-length")
    elif length is None:
        score += 10; reasons.append("unknown-length")
    else:
        score -= 250; reasons.append("empty-length")
    if host == canonical_host:
        score += 40; reasons.append("canonical-host")
    if row["route_class"] in ("homepage", "html_route") or row["path"].lower().startswith(HIGH_VALUE_PREFIXES):
        score += 35; reasons.append("high-value-route")
    score += int(str(row.get("timestamp") or "0")[:14] or "0") / 10**12
    return round(score, 6), reasons


def reject_reasons(row: dict, expected: set[str]) -> list[str]:
    reasons: list[str] = []
    if row.get("statuscode") != 200:
        reasons.append("non-200-status")
    if isinstance(row.get("length"), int) and row["length"] <= 0:
        reasons.append("empty-or-zero-length")
    if row["mime_class"] not in expected:
        reasons.append("unexpected-mime-class")
    if not row.get("timestamp") or not row.get("original_url"):
        reasons.append("missing-required-cdx-field")
    return reasons


def build_outputs(rows: list[dict], context: RunContext) -> tuple[list[dict], list[dict], dict[str, int]]:
    expected = expected_classes(context)
    for row in rows:
        row["selection_score"], row["score_reasons"] = score_record(row, context.config.domain, expected)
        row["reject_reasons"] = reject_reasons(row, expected)
    by_identity: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_identity[row["url_identity"]].append(row)
    chosen = {ident: sorted([r for r in group if not r["reject_reasons"]], key=lambda r: (r["url_identity"], -r["selection_score"], -(int(r.get("timestamp") or 0))))[0] for ident, group in by_identity.items() if any(not r["reject_reasons"] for r in group)}
    used_digest: dict[str, str] = {}
    selected_refs: dict[str, str] = {}
    selections: list[dict] = []
    metrics = {"aliases": 0, "alternates": 0, "rejected": 0, "digest_alias_identities": 0}
    for ident, selected in sorted(chosen.items()):
        digest = selected.get("cdx_digest") or ""
        if digest and digest in used_digest:
            selected_refs[ident] = used_digest[digest]
            metrics["digest_alias_identities"] += 1
            continue
        selection_id = "sel_" + sha256_text(f"{ident}\n{selected.get('timestamp')}\n{selected.get('original_url')}")[:20]
        selected_refs[ident] = selection_id
        if digest:
            used_digest[digest] = selection_id
        group = by_identity[ident]
        selections.append({"run_id": context.run_id, "selection_id": selection_id, "url_identity": ident, "identity_url": selected["identity_url"], "normalized_url": selected["normalized_url"], "selected_original_url": selected["original_url"], "selected_timestamp": selected["timestamp"], "archive_url": f"https://web.archive.org/web/{selected['timestamp']}id_/{selected['original_url']}", "statuscode": selected.get("statuscode"), "mimetype": selected.get("mimetype"), "mime_class": selected["mime_class"], "cdx_digest": digest, "length": selected.get("length"), "selection_score": selected["selection_score"], "selection_reason": "latest-good-" + "-".join(selected["score_reasons"]), "alternate_count": sum(1 for r in group if r is not selected and r.get("cdx_digest") != digest and not r["reject_reasons"]), "alias_count": sum(1 for r in group if r is not selected and (r.get("cdx_digest") == digest or r["identity_url"] == selected["identity_url"])), "output_path_hint": selected["output_path_hint"], "route_class": selected["route_class"], "tags": ["selected", selected["mime_class"], "first-party"]})
    selected_keys = {(s["selected_timestamp"], s["selected_original_url"], s["cdx_digest"]) for s in selections}
    ref_to_selection = {s["selection_id"]: s for s in selections}
    canonical_records: list[dict] = []
    for row in sorted(rows, key=lambda r: (r["url_identity"], r.get("timestamp") or "")):
        ident = row["url_identity"]
        selected_ref = selected_refs.get(ident)
        state = "rejected"
        reason = ";".join(row["reject_reasons"]) if row["reject_reasons"] else "no-selected-candidate"
        if selected_ref and selected_ref in ref_to_selection:
            selected = ref_to_selection[selected_ref]
            if (row.get("timestamp"), row.get("original_url"), row.get("cdx_digest")) in selected_keys:
                state, reason = "selected", "selected-latest-good-representative"
            elif row.get("cdx_digest") == selected.get("cdx_digest") or row["identity_url"] == selected["identity_url"]:
                state, reason = "alias", "same-normalized-route-or-same-cdx-digest"; metrics["aliases"] += 1
            elif not row["reject_reasons"]:
                state, reason = "alternate", "lower-scoring-valid-capture"; metrics["alternates"] += 1
            else:
                metrics["rejected"] += 1
        elif selected_ref:
            state, reason = "alias", "duplicate-cdx-digest-selected-under-another-url-identity"; metrics["aliases"] += 1
        else:
            metrics["rejected"] += 1
        canonical_records.append({"run_id": context.run_id, "record_state": state, "alias_original_url": row.get("original_url"), "alias_timestamp": row.get("timestamp"), "alias_cdx_digest": row.get("cdx_digest"), "canonical_url_identity": ident, "identity_url": row["identity_url"], "normalized_url": row["normalized_url"], "selected_capture_ref": selected_ref, "alias_reason": reason, "statuscode": row.get("statuscode"), "mimetype": row.get("mimetype"), "mime_class": row["mime_class"], "length": row.get("length"), "raw_line_number": row.get("raw_line_number"), "route_class": row["route_class"], "output_path_hint": row["output_path_hint"], "tags": [state]})
    selections.sort(key=lambda s: (s["output_path_hint"], s["identity_url"]))
    return selections, canonical_records, metrics


def report(rows: list[dict], selections: list[dict], canonical_records: list[dict], metrics: dict[str, int], parse_errors: int, context: RunContext) -> str:
    mime_dist = Counter((r.get("mimetype") or "").lower() for r in rows)
    class_dist = Counter(r["mime_class"] for r in rows)
    route_dist = Counter(r["route_class"] for r in rows)
    lines = ["# Selection Report", "", f"Run ID: `{context.run_id}`", "Status: succeeded", f"Generated: `{now_iso()}`", "", "## Summary", "", "| Metric | Value |", "| --- | ---: |", f"| Raw rows | {len(rows)} |", f"| Selected captures | {len(selections)} |", f"| Canonical records | {len(canonical_records)} |", f"| Aliased records | {metrics['aliases']} |", f"| Alternate records | {metrics['alternates']} |", f"| Rejected records | {metrics['rejected']} |", f"| Parse errors | {parse_errors} |", "", "## MIME Distribution", "", "| MIME | Rows |", "| --- | ---: |"]
    lines.extend(f"| `{mime or 'missing'}` | {count} |" for mime, count in mime_dist.most_common(25))
    lines.extend(["", "## MIME Class Distribution", "", "| Class | Rows |", "| --- | ---: |"])
    lines.extend(f"| `{cls}` | {count} |" for cls, count in class_dist.most_common())
    lines.extend(["", "## Top Route Classes", "", "| Route class | Rows |", "| --- | ---: |"])
    lines.extend(f"| `{cls}` | {count} |" for cls, count in route_dist.most_common(20))
    lines.extend(["", "## Notes", "", "- URL identity folds configured aliases into the canonical domain, drops fragments, and preserves query strings.", "- No content was downloaded during this stage."])
    return "\n".join(lines) + "\n"


def run_selection(context: RunContext, *, inventory_path: Path | None = None, selection_path: Path | None = None, canonical_path: Path | None = None, report_path: Path | None = None) -> SelectionResult:
    context.ensure_dirs()
    inventory_path = inventory_path or context.run_dir / "manifests" / "inventory.raw.jsonl"
    selection_path = selection_path or context.run_dir / "manifests" / "selection.pruned.jsonl"
    canonical_path = canonical_path or context.run_dir / "manifests" / "inventory.canonical.jsonl"
    report_path = report_path or context.run_dir / "reports" / "selection-report.md"
    rows, parse_errors = load_rows(inventory_path, context)
    selections, canonical_records, metrics = build_outputs(rows, context)
    write_jsonl(selection_path, selections)
    write_jsonl(canonical_path, canonical_records)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report(rows, selections, canonical_records, metrics, parse_errors, context), encoding="utf-8")
    return SelectionResult(selection_path, canonical_path, report_path, len(rows), len(selections), len(canonical_records))
