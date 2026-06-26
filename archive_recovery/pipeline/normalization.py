from __future__ import annotations

import hashlib
import html
import os
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

from archive_recovery.context import RunContext
from archive_recovery.jsonl import read_jsonl, write_jsonl
from archive_recovery.pipeline.dependencies import CSS_IMPORT_RE, CSS_URL_RE, decode_text, split_srcset
from archive_recovery.pipeline.selection import now_iso


HTML_EXTS = {".html", ".htm", ".php", ".asp", ".aspx"}
TEXT_CLASSES = {"html", "css", "javascript", "json", "xml", "text"}
URL_ATTRS = {"href", "src", "poster", "manifest"}
WAYBACK_URL_RE = re.compile(r"^/(?:web/)?\d{1,14}(?:[a-z_]+)?/(https?://.+)$", re.I)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
WM_IPP_RE = re.compile(r"<(?P<tag>div|section|aside)\b[^>]*\bid\s*=\s*(['\"])wm-ipp\2[^>]*>.*?</(?P=tag)>", re.I | re.S)
WAYBACK_LINK_RE = re.compile(r"<link\b[^>]+href\s*=\s*(['\"])[^'\"]*(?:banner-styles|iconochive)\.css[^'\"]*\1[^>]*>", re.I)
SCRIPT_RE = re.compile(r"<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>", re.I | re.S)
ATTR_RE = re.compile(r"(?P<name>[A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(?P<quote>['\"])(?P<value>.*?)(?P=quote)", re.S)
TAG_RE = re.compile(r"<(?P<close>/)?(?P<tag>[A-Za-z][A-Za-z0-9:-]*)(?P<attrs>[^<>]*?)(?P<slash>/?)>", re.S)


@dataclass(frozen=True)
class NormalizationResult:
    normalization_path: Path
    site_manifest_path: Path
    report_path: Path
    mime_audit_path: Path
    staging_site: Path
    normalized: int
    public_files: int
    collisions: int
    unresolved_internal_links: int


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + f".{os.getpid()}.part")
    part.write_bytes(data)
    os.replace(part, path)


def content_class(record: dict) -> str:
    for value in (record.get("mime_class"), *(record.get("tags") or [])):
        if value in {"html", "css", "javascript", "image", "font", "pdf", "audio", "video", "json", "xml", "text"}:
            return value
    mt = (record.get("response_content_type") or record.get("mimetype") or "").split(";", 1)[0].lower()
    if mt in {"text/html", "application/xhtml+xml"}:
        return "html"
    if mt == "text/css":
        return "css"
    if "javascript" in mt:
        return "javascript"
    if mt.startswith("image/"):
        return "image"
    if mt.startswith("font/"):
        return "font"
    if mt == "application/pdf":
        return "pdf"
    if mt.startswith("audio/"):
        return "audio"
    if mt.startswith("video/"):
        return "video"
    if mt.endswith("+json") or mt == "application/json":
        return "json"
    if mt.endswith("+xml") or mt in {"application/xml", "text/xml"}:
        return "xml"
    if mt.startswith("text/"):
        return "text"
    return "unknown"


def normalized_url(url: str, canonical_host: str, aliases: set[str]) -> str:
    split = urlsplit((url or "").replace("&amp;", "&"))
    scheme = split.scheme.lower() or "http"
    host = (split.hostname or "").lower().rstrip(".")
    if host in aliases or host == "www." + canonical_host:
        host = canonical_host
    netloc = host
    if split.port and not ((scheme == "http" and split.port == 80) or (scheme == "https" and split.port == 443)):
        netloc = f"{host}:{split.port}"
    path = re.sub(r"/{2,}", "/", unquote(split.path or "/"))
    if not path.startswith("/"):
        path = "/" + path
    return urlunsplit((scheme, netloc, path, split.query, ""))


def is_first_party(url: str, canonical_host: str, aliases: set[str]) -> bool:
    split = urlsplit(url)
    host = (split.hostname or "").lower().rstrip(".")
    return split.scheme.lower() in {"http", "https"} and (host == canonical_host or host.endswith("." + canonical_host) or host in aliases or host == "www." + canonical_host)


def unwrap_wayback(url: str) -> str:
    split = urlsplit(url)
    if (split.hostname or "").lower() == "web.archive.org":
        match = re.match(r"^/web/\d{1,14}(?:[a-z_]+)?/(https?://.+)$", split.path, re.I)
        if match:
            return match.group(1) + (("?" + split.query) if split.query else "") + (("#" + split.fragment) if split.fragment else "")
    if not split.scheme:
        match = WAYBACK_URL_RE.match(split.path)
        if match:
            return match.group(1) + (("?" + split.query) if split.query else "") + (("#" + split.fragment) if split.fragment else "")
    return url


def output_base_path(url: str, cls: str, canonical_host: str, aliases: set[str]) -> str:
    split = urlsplit(normalized_url(url, canonical_host, aliases))
    path = re.sub(r"/{2,}", "/", unquote(split.path or "/"))
    query_suffix = f"__q_{sha256_text(split.query)[:8]}" if split.query else ""
    if cls == "html":
        if path == "/":
            stem = ""
        else:
            p = PurePosixPath(path.lstrip("/"))
            suffix = p.suffix.lower()
            if p.name.lower() in {"index.html", "index.htm", "index.php", "default.html", "default.htm"}:
                stem = str(p.parent) if str(p.parent) != "." else ""
            elif suffix in HTML_EXTS:
                stem = str(p.with_suffix(""))
            else:
                stem = str(p)
        if query_suffix:
            stem = f"{stem}{query_suffix}" if stem else query_suffix
        return f"{stem}/index.html" if stem else "index.html"
    rel = path.lstrip("/") or "index"
    if query_suffix:
        p = PurePosixPath(rel)
        rel = str(p.with_name(p.stem + query_suffix + p.suffix))
    return rel


def suffix_collision(path: str, url: str, canonical_host: str, aliases: set[str]) -> str:
    p = PurePosixPath(path)
    suffix = "__u_" + sha256_text(normalized_url(url, canonical_host, aliases))[:8]
    if p.name == "index.html":
        parent = str(p.parent)
        return f"{suffix}/index.html" if parent == "." else f"{parent}{suffix}/index.html"
    return str(p.with_name(p.stem + suffix + p.suffix))


def relative_url(from_path: str, to_path: str, fragment: str = "") -> str:
    rel = os.path.relpath(to_path, start=str(PurePosixPath(from_path).parent)).replace(os.sep, "/")
    if rel == ".":
        rel = PurePosixPath(to_path).name
    return rel + (("#" + fragment) if fragment else "")


def rewrite_reference(value: str, base_url: str, from_path: str, route_map: dict[str, str], canonical_host: str, aliases: set[str], stats: Counter, unresolved: set[str]) -> str:
    raw = html.unescape(value or "").strip()
    if not raw or raw.startswith(("data:", "mailto:", "tel:", "javascript:", "#")):
        return value
    abs_url = unwrap_wayback(urljoin(base_url, raw))
    split = urlsplit(abs_url)
    if is_first_party(abs_url, canonical_host, aliases):
        key = normalized_url(urlunsplit((split.scheme, split.netloc, split.path, split.query, "")), canonical_host, aliases)
        target = route_map.get(key)
        if target:
            stats["links_rewritten"] += 1
            return relative_url(from_path, target, split.fragment)
        stats["unresolved_internal_links"] += 1
        unresolved.add(key)
    elif urlsplit(raw).scheme or raw.startswith("//"):
        stats["external_links_preserved"] += 1
    return value


def rewrite_css_text(css: str, base_url: str, from_path: str, route_map: dict[str, str], canonical_host: str, aliases: set[str], stats: Counter, unresolved: set[str]) -> str:
    def url_repl(match: re.Match) -> str:
        quote_char = match.group("q") or ""
        rewritten = rewrite_reference(match.group("url").strip(), base_url, from_path, route_map, canonical_host, aliases, stats, unresolved)
        return f"url({quote_char}{rewritten}{quote_char})"

    def import_repl(match: re.Match) -> str:
        quote_char = match.group("q")
        rewritten = rewrite_reference(match.group("url").strip(), base_url, from_path, route_map, canonical_host, aliases, stats, unresolved)
        return f"@import {quote_char}{rewritten}{quote_char}"

    return CSS_URL_RE.sub(url_repl, CSS_IMPORT_RE.sub(import_repl, css))


def strip_wayback_artifacts(markup: str, stats: Counter) -> str:
    markup, n = WM_IPP_RE.subn("", markup); stats["artifacts_removed"] += n
    markup, n = WAYBACK_LINK_RE.subn("", markup); stats["artifacts_removed"] += n
    def comment_repl(match: re.Match) -> str:
        text = match.group(0).lower()
        if "wayback" in text and any(token in text for token in ("toolbar", "begin", "end", "internet archive")):
            stats["artifacts_removed"] += 1
            return ""
        return match.group(0)
    markup = COMMENT_RE.sub(comment_repl, markup)
    def script_repl(match: re.Match) -> str:
        text = (match.group("attrs") + match.group("body")).lower()
        if any(token in text for token in ("web.archive.org/_static/", "/_static/js/", "wombat.js", "__wm", "wbinfo", "waybackmachine")):
            stats["artifacts_removed"] += 1
            return ""
        return match.group(0)
    return SCRIPT_RE.sub(script_repl, markup)


def render_attrs(attrs_text: str, updates: dict[str, str | None]) -> str:
    pieces: list[str] = []
    pos = 0
    seen: set[str] = set()
    for match in ATTR_RE.finditer(attrs_text):
        pieces.append(attrs_text[pos:match.start()])
        name = match.group("name")
        lname = name.lower()
        seen.add(lname)
        if lname in updates:
            value = updates[lname]
            if value is not None:
                pieces.append(f'{name}="{html.escape(value, quote=True)}"')
        else:
            pieces.append(match.group(0))
        pos = match.end()
    pieces.append(attrs_text[pos:])
    for name, value in updates.items():
        if value is not None and name not in seen:
            pieces.append(f' {name}="{html.escape(value, quote=True)}"')
    return "".join(pieces)


def rewrite_html(markup: str, base_url: str, from_path: str, route_map: dict[str, str], canonical_host: str, aliases: set[str], stats: Counter, unresolved: set[str]) -> str:
    markup = strip_wayback_artifacts(markup, stats)

    def tag_repl(match: re.Match) -> str:
        if match.group("close"):
            return match.group(0)
        tag = match.group("tag").lower()
        attrs = match.group("attrs") or ""
        found = {m.group("name").lower(): m.group("value") for m in ATTR_RE.finditer(attrs)}
        updates: dict[str, str | None] = {}
        if tag == "form":
            original = found.get("action", "")
            if original:
                updates["data-original-action"] = original
            updates.update({"action": "#", "method": "get", "onsubmit": "return false"})
            stats["forms_neutralized"] += 1
        for attr in URL_ATTRS:
            if attr in found and not (tag == "form" and attr == "action"):
                updates[attr] = rewrite_reference(found[attr], base_url, from_path, route_map, canonical_host, aliases, stats, unresolved)
        if "srcset" in found:
            parts = []
            for src in split_srcset(found["srcset"]):
                parts.append(rewrite_reference(src, base_url, from_path, route_map, canonical_host, aliases, stats, unresolved))
            updates["srcset"] = ", ".join(parts)
        if "style" in found:
            updates["style"] = rewrite_css_text(found["style"], base_url, from_path, route_map, canonical_host, aliases, stats, unresolved)
        return f"<{match.group('tag')}{render_attrs(attrs, updates)}{match.group('slash')}>"

    markup = TAG_RE.sub(tag_repl, markup)
    markup = re.sub(r"<style\b([^>]*)>(.*?)</style\s*>", lambda m: f"<style{m.group(1)}>" + rewrite_css_text(m.group(2), base_url, from_path, route_map, canonical_host, aliases, stats, unresolved) + "</style>", markup, flags=re.I | re.S)
    return markup


def transform(record: dict, from_path: str, route_map: dict[str, str], canonical_host: str, aliases: set[str]) -> tuple[bytes, Counter, list[str], str | None]:
    raw = Path(record["raw_path"]).read_bytes()
    cls = record["content_class"]
    if cls in {"html", "css"}:
        text = decode_text(raw, record.get("response_content_type"))
        stats: Counter = Counter(); unresolved: set[str] = set()
        if cls == "html":
            out = rewrite_html(text, record["original_url"], from_path, route_map, canonical_host, aliases, stats, unresolved)
        else:
            out = rewrite_css_text(text, record["original_url"], from_path, route_map, canonical_host, aliases, stats, unresolved)
        return out.encode("utf-8"), stats, sorted(unresolved), "utf-8"
    return raw, Counter(), [], None


def route_keys(item: dict, canonical_host: str, aliases: set[str]) -> set[str]:
    keys = set()
    for value in (item.get("original_url"), item.get("selected_original_url"), item.get("alias_original_url"), item.get("normalized_url"), item.get("identity_url")):
        if value:
            keys.add(normalized_url(value, canonical_host, aliases))
    return keys


def run_normalize(context: RunContext, *, selection_path: Path | None = None, canonical_path: Path | None = None, download_path: Path | None = None, staging_site: Path | None = None, normalization_path: Path | None = None, site_manifest_path: Path | None = None, report_path: Path | None = None, mime_audit_path: Path | None = None) -> NormalizationResult:
    context.ensure_dirs()
    selection_path = selection_path or context.run_dir / "manifests" / "selection.pruned.jsonl"
    canonical_path = canonical_path or context.run_dir / "manifests" / "inventory.canonical.jsonl"
    download_path = download_path or context.run_dir / "manifests" / "download.results.jsonl"
    staging_site = staging_site or context.staging_site
    normalization_path = normalization_path or context.run_dir / "manifests" / "normalization.results.jsonl"
    site_manifest_path = site_manifest_path or context.run_dir / "manifests" / "site.manifest.jsonl"
    report_path = report_path or context.run_dir / "reports" / "normalization-report.md"
    mime_audit_path = mime_audit_path or context.run_dir / "reports" / "mime-audit.md"
    canonical_host = context.config.domain.lower(); aliases = {h.lower() for h in context.config.alias_hosts}
    selections = {r.get("selection_id"): r for r in read_jsonl(selection_path) if r.get("selection_id")}
    downloads = [r for r in read_jsonl(download_path) if r.get("fetch_state") == "succeeded" and r.get("validation_state") == "valid" and r.get("raw_path")]
    canonical_rows = list(read_jsonl(canonical_path)) if canonical_path.exists() else []

    items: list[dict] = []
    for dl in downloads:
        merged = dict(selections.get(dl.get("job_id"), {})); merged.update(dl)
        merged["content_class"] = merged.get("mime_class") or content_class(merged)
        merged["base_output_path"] = output_base_path(merged.get("normalized_url") or merged.get("original_url") or "", merged["content_class"], canonical_host, aliases)
        items.append(merged)
    items.sort(key=lambda r: (r["base_output_path"], normalized_url(r.get("original_url") or "", canonical_host, aliases), r.get("requested_timestamp") or "", r.get("raw_sha256") or ""))

    base_route: dict[str, str] = {}
    for item in items:
        for key in route_keys(item, canonical_host, aliases):
            base_route[key] = item["base_output_path"]
    by_ref = {i.get("selection_id") or i.get("job_id"): i for i in items}
    for alias in canonical_rows:
        target = by_ref.get(alias.get("selected_capture_ref"))
        if target:
            for key in route_keys(alias, canonical_host, aliases):
                base_route[key] = target["base_output_path"]

    path_groups: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        data, stats, unresolved, encoding = transform(item, item["base_output_path"], base_route, canonical_host, aliases)
        item.update({"first_final_sha256": sha256_bytes(data), "first_stats": stats, "first_unresolved": unresolved, "encoding": encoding})
        path_groups[item["base_output_path"]].append(item)
    collisions: list[dict] = []
    for path, group in path_groups.items():
        by_hash: dict[str, list[dict]] = defaultdict(list)
        for item in group:
            by_hash[item["first_final_sha256"]].append(item)
        if len(by_hash) == 1:
            for item in group:
                item["output_path"] = path; item["collision_status"] = "duplicate-same-content" if len(group) > 1 else "none"
        else:
            owner = sorted(by_hash)[0]
            for item in group:
                if item["first_final_sha256"] == owner:
                    item["output_path"] = path; item["collision_status"] = "collision-owner"
                else:
                    item["output_path"] = suffix_collision(path, item.get("normalized_url") or item.get("original_url") or path, canonical_host, aliases); item["collision_status"] = "collision-suffixed"
                    collisions.append({"base_output_path": path, "output_path": item["output_path"], "source_url": item.get("original_url")})

    final_route = dict(base_route)
    for item in items:
        for key in route_keys(item, canonical_host, aliases):
            final_route[key] = item["output_path"]
    for alias in canonical_rows:
        target = by_ref.get(alias.get("selected_capture_ref"))
        if target and target.get("output_path"):
            for key in route_keys(alias, canonical_host, aliases):
                final_route[key] = target["output_path"]

    if staging_site.exists():
        for child in staging_site.iterdir():
            shutil.rmtree(child) if child.is_dir() and not child.is_symlink() else child.unlink()
    staging_site.mkdir(parents=True, exist_ok=True)

    normalization_records: list[dict] = []; site_by_path: dict[str, dict] = {}; unresolved_all: set[str] = set(); mime_counter: Counter = Counter()
    transform_version = "wayback-cleanup-v1"
    for item in items:
        data, stats, unresolved, encoding = transform(item, item["output_path"], final_route, canonical_host, aliases)
        final_sha = sha256_bytes(data); output_path = item["output_path"]
        if output_path not in site_by_path:
            atomic_write_bytes(staging_site / output_path, data)
            site_by_path[output_path] = {"run_id": context.run_id, "output_path": output_path, "source_url": item.get("original_url"), "normalized_url": item.get("normalized_url"), "timestamp": item.get("requested_timestamp") or item.get("selected_timestamp"), "archive_url": item.get("archive_url"), "raw_sha256": item.get("raw_sha256"), "final_sha256": final_sha, "content_class": item["content_class"], "response_content_type": item.get("response_content_type"), "transform_version": transform_version, "provenance_ref": item.get("job_id"), "tags": sorted(set(item.get("tags") or []) | {"normalized"})}
        unresolved_all.update(unresolved); mime_counter[item["content_class"]] += 1
        normalization_records.append({"run_id": context.run_id, "original_url": item.get("original_url"), "normalized_url": item.get("normalized_url"), "timestamp": item.get("requested_timestamp") or item.get("selected_timestamp"), "archive_url": item.get("archive_url"), "raw_sha256": item.get("raw_sha256"), "final_sha256": final_sha, "output_path": output_path, "content_class": item["content_class"], "transform_version": transform_version, "artifacts_removed": int(stats.get("artifacts_removed", 0)), "forms_neutralized": int(stats.get("forms_neutralized", 0)), "links_rewritten": int(stats.get("links_rewritten", 0)), "unresolved_internal_links": len(unresolved), "unresolved_internal_link_targets": unresolved[:25], "external_links_preserved": int(stats.get("external_links_preserved", 0)), "collision_status": item["collision_status"], "normalization_state": "succeeded", "encoding": encoding, "tags": sorted(set(item.get("tags") or []) | {"normalized"})})

    site_records = [site_by_path[p] for p in sorted(site_by_path)]
    write_jsonl(normalization_path, normalization_records); write_jsonl(site_manifest_path, site_records)
    failed = len([r for r in read_jsonl(download_path) if r.get("fetch_state") != "succeeded" or r.get("validation_state") != "valid"])
    ts = now_iso()
    report_lines = ["# Normalization Report", "", f"Run ID: `{context.run_id}`", "Status: succeeded", f"Updated: {ts}", "", f"Downloaded inputs normalized: {len(normalization_records)}", f"Public files written: {len(site_records)}", f"Failed/skipped download inputs: {failed}", f"Output path collisions suffixed: {len(collisions)}", f"Distinct unresolved internal links: {len(unresolved_all)}", f"Transform version: `{transform_version}`", "", "## Collision Records", ""]
    report_lines.extend([f"- `{c['base_output_path']}` -> `{c['output_path']}` from `{c['source_url']}`" for c in collisions[:100]] or ["_none_"])
    report_lines.extend(["", "## Unresolved Internal Links", ""]); report_lines.extend([f"- `{u}`" for u in sorted(unresolved_all)[:200]] or ["_none_"])
    report_path.parent.mkdir(parents=True, exist_ok=True); report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    mime_lines = ["# Mime Audit", "", f"Run ID: `{context.run_id}`", "Status: updated by normalization", f"Updated: {ts}", "", "## Normalized Content Classes", ""]
    mime_lines.extend(f"- {k}: {v}" for k, v in sorted(mime_counter.items()))
    mime_audit_path.parent.mkdir(parents=True, exist_ok=True); mime_audit_path.write_text("\n".join(mime_lines) + "\n", encoding="utf-8")
    return NormalizationResult(normalization_path, site_manifest_path, report_path, mime_audit_path, staging_site, len(normalization_records), len(site_records), len(collisions), len(unresolved_all))
