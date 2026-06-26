from __future__ import annotations

import json
import mimetypes
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlsplit, unquote

from archive_recovery.context import RunContext
from archive_recovery.jsonl import read_jsonl
from archive_recovery.pipeline.dependencies import ReferenceParser, css_refs, decode_text
from archive_recovery.pipeline.selection import now_iso


HTML_EXTS = {".html", ".htm"}
TEXT_PREFIXES = (b"<!doctype html", b"<html", b"<?xml", b"body", b".", b"#", b"@import")


@dataclass(frozen=True)
class ValidationResult:
    report_path: Path
    external_links_path: Path
    checked_files: int
    internal_references: int
    missing_references: int
    external_references: int
    mime_warnings: int


def public_paths(site_root: Path) -> set[str]:
    return {p.relative_to(site_root).as_posix() for p in site_root.rglob("*") if p.is_file() and not p.is_symlink()}


def resolve_internal_path(from_path: str, raw_ref: str, site_paths: set[str]) -> str | None:
    if not raw_ref or raw_ref.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    parts = urlsplit(raw_ref)
    if parts.scheme or parts.netloc:
        return None
    base = "/" + str(PurePosixPath(from_path).parent) + "/"
    normalized = urlsplit(urljoin(base, raw_ref)).path
    rel = unquote(normalized).lstrip("/") or "index.html"
    candidates = [rel]
    if rel.endswith("/"):
        candidates.append(rel + "index.html")
    elif not PurePosixPath(rel).suffix:
        candidates.extend([rel + "/index.html", rel + ".html"])
    return next((candidate for candidate in candidates if candidate in site_paths), rel)


def extract_refs(path: Path, content_class: str) -> list[tuple[str, str, str | None]]:
    data = path.read_bytes()
    if content_class == "html":
        parser = ReferenceParser(); parser.feed(decode_text(data, "text/html")); return parser.refs
    if content_class == "css":
        return [("css", kind, value) for kind, value in css_refs(decode_text(data, "text/css"))]
    return []


def is_external(raw_ref: str | None) -> bool:
    if not raw_ref:
        return False
    parts = urlsplit(raw_ref)
    return bool(parts.scheme in {"http", "https"} or raw_ref.startswith("//"))


def expected_class_from_path(path: str) -> str:
    suffix = PurePosixPath(path).suffix.lower()
    if suffix in HTML_EXTS:
        return "html"
    if suffix == ".css":
        return "css"
    if suffix in {".js", ".mjs"}:
        return "javascript"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}:
        return "image"
    if suffix in {".woff", ".woff2", ".ttf", ".otf", ".eot"}:
        return "font"
    if suffix == ".pdf":
        return "pdf"
    return "unknown"


def mime_warnings_for(path: Path, content_class: str) -> list[str]:
    warnings: list[str] = []
    guessed = mimetypes.guess_type(path.name)[0] or ""
    suffix_class = expected_class_from_path(path.name)
    if suffix_class != "unknown" and content_class != "unknown" and suffix_class != content_class and not (suffix_class == "javascript" and content_class == "text"):
        warnings.append(f"extension suggests {suffix_class}, manifest says {content_class}")
    prefix = path.read_bytes()[:256].lstrip().lower()
    if content_class in {"image", "font", "pdf", "audio", "video"} and any(prefix.startswith(p) for p in TEXT_PREFIXES):
        warnings.append("binary class appears to contain text/html/css")
    if content_class == "html" and prefix and not (prefix.startswith(b"<!doctype") or prefix.startswith(b"<html") or b"<html" in prefix):
        warnings.append("html class does not look like html")
    if guessed and content_class == "css" and guessed != "text/css":
        warnings.append(f"extension MIME guess is {guessed}")
    return warnings


def run_validate(context: RunContext, *, staging_site: Path | None = None, site_manifest_path: Path | None = None, report_path: Path | None = None, external_links_path: Path | None = None) -> ValidationResult:
    context.ensure_dirs()
    staging_site = staging_site or context.staging_site
    site_manifest_path = site_manifest_path or context.run_dir / "manifests" / "site.manifest.jsonl"
    report_path = report_path or context.run_dir / "reports" / "validation-report.md"
    external_links_path = external_links_path or context.run_dir / "reports" / "external-links.json"
    site_paths = public_paths(staging_site)
    manifest = list(read_jsonl(site_manifest_path))
    manifest_by_path = {r.get("output_path"): r for r in manifest}
    missing_files = [p for p in manifest_by_path if p and p not in site_paths]
    extra_files = sorted(site_paths - set(manifest_by_path))
    missing_refs: list[dict] = []
    external_refs: list[dict] = []
    mime_findings: list[dict] = []
    checked = 0; internal_count = 0

    for output_path, row in sorted(manifest_by_path.items()):
        if not output_path or output_path not in site_paths:
            continue
        path = staging_site / output_path
        cls = row.get("content_class") or expected_class_from_path(output_path)
        warnings = mime_warnings_for(path, cls)
        if warnings:
            mime_findings.append({"path": output_path, "content_class": cls, "warnings": warnings})
        refs = extract_refs(path, cls)
        if refs:
            checked += 1
        for tag, attr, raw in refs:
            raw_value = (raw or "").strip()
            if is_external(raw_value):
                external_refs.append({"source": output_path, "context": tag, "attribute": attr, "url": raw_value})
                continue
            resolved = resolve_internal_path(output_path, raw_value, site_paths)
            if resolved is None:
                continue
            internal_count += 1
            if resolved not in site_paths:
                missing_refs.append({"source": output_path, "context": tag, "attribute": attr, "reference": raw_value, "resolved_path": resolved})

    status = "succeeded" if not missing_files and not missing_refs else "issues-found"
    counts = Counter(r.get("content_class") or "unknown" for r in manifest)
    ts = now_iso()
    lines = ["# Validation Report", "", f"Run ID: `{context.run_id}`", f"Status: {status}", f"Updated: {ts}", "", "## Summary", "", f"- Public files in manifest: {len(manifest)}", f"- Files present in staging: {len(site_paths)}", f"- Parsed HTML/CSS files: {checked}", f"- Internal references checked: {internal_count}", f"- Missing internal references/assets: {len(missing_refs)}", f"- External references: {len(external_refs)}", f"- MIME/content warnings: {len(mime_findings)}", f"- Manifest files missing from staging: {len(missing_files)}", f"- Extra staging files not in manifest: {len(extra_files)}", "", "## Content Classes", ""]
    lines.extend(f"- {key}: {value}" for key, value in sorted(counts.items()))
    lines.extend(["", "## Missing Internal References", ""])
    lines.extend([f"- `{r['source']}` {r['attribute']}=`{r['reference']}` -> `{r['resolved_path']}`" for r in missing_refs[:200]] or ["_none_"])
    lines.extend(["", "## MIME/Content Warnings", ""])
    lines.extend([f"- `{r['path']}`: {', '.join(r['warnings'])}" for r in mime_findings[:200]] or ["_none_"])
    report_path.parent.mkdir(parents=True, exist_ok=True); report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    external_links_path.parent.mkdir(parents=True, exist_ok=True); external_links_path.write_text(json.dumps({"run_id": context.run_id, "generated_at": ts, "external_links": external_refs}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ValidationResult(report_path, external_links_path, checked, internal_count, len(missing_refs), len(external_refs), len(mime_findings))
