from __future__ import annotations

import hashlib
import html
import re
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, quote, unquote, urljoin, urlsplit, urlunsplit

from archive_recovery.context import RunContext
from archive_recovery.jsonl import read_jsonl, write_jsonl
from archive_recovery.pipeline.selection import now_iso


HTML_URL_ATTRS = {"href", "src", "poster", "action", "manifest"}
SRCSET_ATTRS = {"srcset"}
CSS_URL_RE = re.compile(r"url\(\s*(?P<q>['\"]?)(?P<url>.*?)(?P=q)\s*\)", re.I | re.S)
CSS_IMPORT_RE = re.compile(r"@import\s+(?:url\(\s*)?(?P<q>['\"])(?P<url>.*?)(?P=q)", re.I | re.S)
CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
WAYBACK_PREFIX_RE = re.compile(r"^https?://web\.archive\.org/web/\d+(?:[a-z_]+)?/", re.I)
INDEX_RE = re.compile(r"/(?:index|default)\.(?:html?|php|asp|aspx)$", re.I)
TRACKING_PARAMS = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid")
ASSET_EXT_CLASSES = {".css": "css", ".js": "javascript", ".mjs": "javascript", ".jpg": "image", ".jpeg": "image", ".png": "image", ".gif": "image", ".webp": "image", ".svg": "image", ".ico": "image", ".bmp": "image", ".tif": "image", ".tiff": "image", ".woff": "font", ".woff2": "font", ".ttf": "font", ".otf": "font", ".eot": "font", ".pdf": "pdf", ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".m4a": "audio", ".mp4": "video", ".webm": "video", ".mov": "video", ".json": "json", ".xml": "xml", ".rss": "xml"}
HIGH_VALUE_PREFIXES = ("/wp-content/", "/assets/", "/images/", "/img/", "/css/", "/js/", "/scripts/", "/audio/", "/video/")


@dataclass(frozen=True)
class DependencyResult:
    graph_path: Path
    missing_path: Path
    report_path: Path
    parsed_files: int
    references: int
    missing: int


def decode_text(data: bytes, content_type: str | None) -> str:
    match = re.search(r"charset=([^;\s]+)", content_type or "", re.I)
    candidates = [match.group(1).strip('"') if match else None, "utf-8", "windows-1252", "latin-1"]
    for enc in candidates:
        if not enc:
            continue
        try:
            return data.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return data.decode("utf-8", errors="replace")


def clean_url_value(value: object) -> str | None:
    if value is None:
        return None
    value = html.unescape(str(value)).strip()
    if not value or value.startswith(("#", "javascript:", "mailto:", "tel:", "data:", "about:")):
        return None
    return WAYBACK_PREFIX_RE.sub("", value)


def split_srcset(value: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    in_quote = None
    for ch in value:
        if ch in "'\"":
            in_quote = None if in_quote == ch else ch if in_quote is None else in_quote
        if ch == "," and in_quote is None:
            item = "".join(current).strip()
            if item:
                items.append(item.split()[0])
            current = []
        else:
            current.append(ch)
    item = "".join(current).strip()
    if item:
        items.append(item.split()[0])
    return items


def css_refs(css_text: str):
    text = CSS_COMMENT_RE.sub("", css_text)
    for match in CSS_IMPORT_RE.finditer(text):
        yield "css_import", match.group("url")
    for match in CSS_URL_RE.finditer(text):
        yield "css_url", match.group("url")


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle(tag, attrs)

    def _handle(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value for name, value in attrs if name}
        for attr, value in attr_map.items():
            if attr in HTML_URL_ATTRS:
                self.refs.append((tag.lower(), attr, value))
            elif attr in SRCSET_ATTRS:
                for src in split_srcset(value or ""):
                    self.refs.append((tag.lower(), attr, src))
            elif attr == "style":
                for kind, ref in css_refs(value or ""):
                    self.refs.append((tag.lower(), kind, ref))


def normalize_path(path: str) -> str:
    path = unquote(path or "/")
    path = re.sub(r"/{2,}", "/", path)
    if not path.startswith("/"):
        path = "/" + path
    return quote(path, safe="/%:@!$&'()*+,;=-._~")


def filtered_query(query: str) -> str:
    pairs = []
    for key, value in parse_qsl(query, keep_blank_values=True):
        if key.lower().startswith(TRACKING_PARAMS):
            continue
        pairs.append((key, value))
    return "&".join(f"{quote(k, safe='')}={quote(v, safe='')}" if v != "" else quote(k, safe="") for k, v in pairs)


def canonical_forms(url: str, canonical_host: str, alias_hosts: set[str]) -> set[str]:
    parts = urlsplit(url)
    if not parts.scheme and not parts.netloc:
        return set()
    scheme = (parts.scheme or "http").lower()
    host = (parts.hostname or "").lower().rstrip(".")
    if host in alias_hosts or host == "www." + canonical_host:
        host = canonical_host
    path = normalize_path(parts.path)
    query = filtered_query(parts.query)
    forms = {urlunsplit((s, host, path, query, "")) for s in {scheme, "https", "http"}}
    index_path = INDEX_RE.sub("/", path)
    if index_path != path:
        forms.update({urlunsplit(("https", host, index_path, query, "")), urlunsplit(("http", host, index_path, query, ""))})
    if not Path(path).suffix and not path.endswith("/"):
        forms.update({urlunsplit(("https", host, path + "/", query, "")), urlunsplit(("http", host, path + "/", query, ""))})
    if path.endswith("/"):
        no_slash = path.rstrip("/") or "/"
        forms.update({urlunsplit(("https", host, no_slash, query, "")), urlunsplit(("http", host, no_slash, query, ""))})
    return forms


def identity_hash(forms: set[str]) -> str | None:
    return hashlib.sha256(min(forms).encode("utf-8")).hexdigest() if forms else None


def classify_url(url: str, canonical_host: str, alias_hosts: set[str]) -> str:
    parts = urlsplit(url)
    if parts.scheme and parts.scheme.lower() not in {"http", "https"}:
        return "non-http"
    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        return "first-party"
    return "first-party" if host == canonical_host or host.endswith("." + canonical_host) or host in alias_hosts or host == "www." + canonical_host else "external"


def guess_class(url: str) -> str:
    suffix = Path(urlsplit(url).path).suffix.lower()
    if suffix in ASSET_EXT_CLASSES:
        return ASSET_EXT_CLASSES[suffix]
    if not suffix or suffix in {".html", ".htm", ".php", ".asp", ".aspx"}:
        return "html"
    return "unknown"


def high_value_missing(url: str) -> bool:
    path = (urlsplit(url).path or "/").lower()
    cls = guess_class(url)
    return cls in {"css", "javascript", "image", "font", "audio", "video", "pdf", "json", "xml"} or path.startswith(HIGH_VALUE_PREFIXES)


def build_selected_index(selections: list[dict], canonical_host: str, alias_hosts: set[str]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for row in selections:
        forms: set[str] = set()
        for value in (row.get("selected_original_url"), row.get("normalized_url"), row.get("identity_url")):
            if value:
                forms.update(canonical_forms(value, canonical_host, alias_hosts))
        for form in forms:
            index[form] = row
        if row.get("url_identity"):
            index[row["url_identity"]] = row
    return index


def discover_references(source_text: str, mime_class: str) -> list[tuple[str, str, str | None]]:
    if mime_class == "html":
        parser = ReferenceParser(); parser.feed(source_text); return parser.refs
    if mime_class == "css":
        return [("css", kind, value) for kind, value in css_refs(source_text)]
    return []


def raw_bytes(path_value: str) -> bytes:
    path = Path(path_value)
    return path.read_bytes()


def make_graph_and_missing(context: RunContext, selections: list[dict], downloads: list[dict]) -> tuple[list[dict], list[dict], int, int]:
    canonical_host = context.config.domain.lower()
    alias_hosts = {h.lower() for h in context.config.alias_hosts}
    selected_index = build_selected_index(selections, canonical_host, alias_hosts)
    selection_by_id = {s["selection_id"]: s for s in selections if s.get("selection_id")}
    graph: list[dict] = []
    missing_seen: dict[str, dict] = {}
    parsed_files = 0; parse_errors = 0
    for row in downloads:
        if row.get("fetch_state") != "succeeded" or row.get("validation_state") != "valid" or not row.get("raw_path"):
            continue
        selected = selection_by_id.get(row.get("job_id"), {})
        content_type = row.get("response_content_type") or selected.get("mimetype") or ""
        mime_class = selected.get("mime_class") or ("html" if "html" in content_type else "css" if "css" in content_type else "")
        if mime_class not in {"html", "css"}:
            continue
        try:
            refs = discover_references(decode_text(raw_bytes(row["raw_path"]), content_type), mime_class)
            parsed_files += 1
        except Exception:
            parse_errors += 1
            continue
        for idx, (tag, attr, raw_value) in enumerate(refs, 1):
            cleaned = clean_url_value(raw_value)
            if not cleaned:
                continue
            resolved = urljoin(row["original_url"], cleaned)
            scope = classify_url(resolved, canonical_host, alias_hosts)
            forms = canonical_forms(resolved, canonical_host, alias_hosts)
            matched = next((selected_index[f] for f in forms if f in selected_index), None)
            if not matched and identity_hash(forms) in selected_index:
                matched = selected_index[identity_hash(forms)]  # type: ignore[index]
            status = "resolved" if matched else "externalized" if scope != "first-party" else "missing"
            norm = min(forms) if forms else resolved
            rec = {"run_id": context.run_id, "source_selection_id": row.get("job_id"), "source_original_url": row.get("original_url"), "source_raw_sha256": row.get("raw_sha256"), "source_mime_class": mime_class, "reference_index": idx, "reference_context": tag, "reference_attribute": attr, "raw_reference": raw_value, "resolved_url": resolved, "normalized_url": norm, "scope": scope, "target_mime_guess": guess_class(resolved), "resolution_state": status, "target_selection_id": matched.get("selection_id") if matched else None, "target_identity_url": matched.get("identity_url") if matched else None, "url_identity": matched.get("url_identity") if matched else identity_hash(forms)}
            graph.append(rec)
            if status == "missing":
                entry = missing_seen.setdefault(norm, {"run_id": context.run_id, "request_id": "dep_" + hashlib.sha256(norm.encode("utf-8")).hexdigest()[:20], "stage_requesting": "dependencies", "requested_stage": "inventory.dependencies", "original_url": resolved, "normalized_url": norm, "url_identity": rec["url_identity"], "scope": "first-party", "target_mime_guess": rec["target_mime_guess"], "high_value": high_value_missing(resolved), "reason": "first-party-static-reference-not-selected", "source_count": 0, "source_examples": []})
                entry["source_count"] += 1
                if len(entry["source_examples"]) < 5:
                    entry["source_examples"].append(row.get("original_url"))
    graph.sort(key=lambda r: (r["source_original_url"] or "", r["reference_index"], r["resolved_url"]))
    missing = sorted(missing_seen.values(), key=lambda r: (not r["high_value"], r["target_mime_guess"], r["normalized_url"]))
    return graph, missing, parsed_files, parse_errors


def report(context: RunContext, graph: list[dict], missing: list[dict], parsed_files: int, parse_errors: int) -> str:
    states = Counter(r["resolution_state"] for r in graph)
    scopes = Counter(r["scope"] for r in graph)
    missing_classes = Counter(r["target_mime_guess"] for r in missing)
    high_missing = [r for r in missing if r["high_value"]]
    lines = ["# Dependency Report", "", f"Run ID: `{context.run_id}`", "Status: succeeded", f"Generated: `{now_iso()}`", "", "## Summary", "", "| Metric | Value |", "| --- | ---: |", f"| Parsed HTML/CSS files | {parsed_files} |", f"| Parse errors | {parse_errors} |", f"| Dependency references | {len(graph)} |", f"| Resolved first-party references | {states['resolved']} |", f"| Externalized references | {states['externalized']} |", f"| Unresolved first-party URLs | {len(missing)} |", f"| High-value missing assets | {len(high_missing)} |", "", "## Reference Scope", ""]
    lines.extend(f"- {key}: {value}" for key, value in sorted(scopes.items()))
    lines.extend(["", "## Missing By Class", ""])
    lines.extend([f"- {key}: {value}" for key, value in missing_classes.most_common()] or ["- none"])
    lines.extend(["", "## High-Value Missing", ""])
    lines.extend([f"- `{rec['normalized_url']}` ({rec['target_mime_guess']}, {rec['source_count']} refs)" for rec in high_missing[:50]] or ["- none"])
    lines.extend(["", "## Notes", "", "- Static extraction only; JavaScript was not executed."])
    return "\n".join(lines) + "\n"


def run_dependencies(context: RunContext, *, selection_path: Path | None = None, download_path: Path | None = None, graph_path: Path | None = None, missing_path: Path | None = None, report_path: Path | None = None) -> DependencyResult:
    context.ensure_dirs()
    selection_path = selection_path or context.run_dir / "manifests" / "selection.pruned.jsonl"
    download_path = download_path or context.run_dir / "manifests" / "download.results.jsonl"
    graph_path = graph_path or context.run_dir / "manifests" / "dependency-graph.jsonl"
    missing_path = missing_path or context.run_dir / "manifests" / "missing-dependency-requests.jsonl"
    report_path = report_path or context.run_dir / "reports" / "dependency-report.md"
    graph, missing, parsed, errors = make_graph_and_missing(context, list(read_jsonl(selection_path)), list(read_jsonl(download_path)))
    write_jsonl(graph_path, graph)
    write_jsonl(missing_path, missing)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report(context, graph, missing, parsed, errors), encoding="utf-8")
    return DependencyResult(graph_path, missing_path, report_path, parsed, len(graph), len(missing))
