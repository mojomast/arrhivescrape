from __future__ import annotations

import hashlib
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .fs import iter_artifacts, load_frozen_config, safe_child


TEXT_EXTENSIONS = {
    ".css",
    ".csv",
    ".htm",
    ".html",
    ".js",
    ".json",
    ".jsonl",
    ".log",
    ".md",
    ".toml",
    ".txt",
    ".svg",
    ".xml",
}
TEXT_MIME_PREFIXES = ("text/",)
TEXT_MIME_TYPES = {
    "application/ecmascript",
    "application/javascript",
    "application/json",
    "application/ld+json",
    "application/toml",
    "application/xml",
    "application/x-javascript",
    "application/x-ndjson",
}
IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
AUDIO_MIME_TYPES = {"audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav", "audio/webm"}
VIDEO_MIME_TYPES = {"video/mp4", "video/ogg", "video/webm"}

SCHEMA_HINTS = {
    "inventory.raw.jsonl": "inventory",
    "selection.pruned.jsonl": "selection",
    "inventory.canonical.jsonl": "canonical-inventory",
    "download.results.jsonl": "download-results",
    "dependency-graph.jsonl": "dependency-graph",
    "missing-dependency-requests.jsonl": "missing-dependencies",
    "normalization.results.jsonl": "normalization-results",
    "site.manifest.jsonl": "site-manifest",
    "events.jsonl": "events",
    "external-links.json": "external-links",
}


def _jsonl(path: Path) -> Iterable[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    yield value
    except OSError:
        return


def _iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")


def stable_object_id(kind: str, path: str, digest: str = "") -> str:
    material = f"{kind}\0{path}\0{digest}".encode("utf-8", "surrogatepass")
    return hashlib.sha256(material).hexdigest()[:32]


def media_type_for(path: Path, explicit: str | None = None) -> str:
    if explicit:
        return explicit.split(";", 1)[0].strip().lower()
    guessed, _ = mimetypes.guess_type(path.name)
    return (guessed or "application/octet-stream").lower()


def classify_preview(path: Path, media_type: str, content_class: str | None = None) -> str:
    """Return the only inline preview category allowed for this object."""

    suffix = path.suffix.lower()
    mime = media_type.split(";", 1)[0].strip().lower()
    klass = (content_class or "").lower()
    if mime in IMAGE_MIME_TYPES:
        return "image"
    if mime in AUDIO_MIME_TYPES:
        return "audio"
    if mime in VIDEO_MIME_TYPES:
        return "video"
    if suffix in TEXT_EXTENSIONS or mime in TEXT_MIME_TYPES or mime.startswith(TEXT_MIME_PREFIXES) or klass in {"html", "css", "javascript", "json", "text", "xml"}:
        # Source is always served as text/plain with a strict CSP, never as a live document.
        return "source"
    return "none"


def schema_hint_for(display_path: str) -> str:
    name = Path(display_path).name.lower()
    return SCHEMA_HINTS.get(name, "")


def renderer_for(path: Path, media_type: str, content_class: str | None = None, display_path: str = "") -> str:
    """Return a safe UI renderer hint without changing raw preview rules."""

    suffix = path.suffix.lower()
    mime = media_type.split(";", 1)[0].strip().lower()
    schema = schema_hint_for(display_path)
    preview = classify_preview(path, media_type, content_class)
    if schema:
        return schema
    if suffix == ".md":
        return "markdown"
    if suffix == ".jsonl" or mime == "application/x-ndjson":
        return "jsonl"
    if suffix == ".json" or mime in {"application/json", "application/ld+json"}:
        return "json"
    if suffix == ".log":
        return "log"
    if mime == "application/pdf" or suffix == ".pdf":
        return "pdf-metadata"
    if mime == "image/svg+xml" or suffix == ".svg":
        return "svg-source"
    if preview in {"image", "audio", "video"}:
        return preview
    if preview == "source":
        return "text"
    return "binary"


def _content_class(path: Path, media_type: str, value: Any = None) -> str:
    if isinstance(value, str) and value:
        return value
    category = classify_preview(path, media_type)
    if category == "source":
        return "text"
    if category in {"image", "audio", "video"}:
        return category
    return "binary"


def _public(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if not key.startswith("_")}


def _record(run_dir: Path, *, kind: str, stage: str, file_path: Path, display_path: str, metadata: dict[str, Any] | None = None, id_path: str | None = None) -> dict[str, Any] | None:
    try:
        resolved = file_path.resolve()
        stat = resolved.stat()
    except OSError:
        return None
    meta = metadata or {}
    media_type = media_type_for(resolved, meta.get("media_type") or meta.get("mime") or meta.get("mimetype") or meta.get("response_content_type"))
    content_class = _content_class(resolved, media_type, meta.get("content_class") or meta.get("mime_class"))
    raw_sha = meta.get("raw_sha256") if isinstance(meta.get("raw_sha256"), str) else None
    final_sha = meta.get("final_sha256") if isinstance(meta.get("final_sha256"), str) else None
    oid = stable_object_id(kind, id_path or display_path, raw_sha or final_sha or "")
    warnings = [str(item) for item in meta.get("warnings", []) if item] if isinstance(meta.get("warnings"), list) else []
    return {
        "object_id": oid,
        "kind": kind,
        "stage": stage,
        "path": display_path,
        "display_path": display_path,
        "size": stat.st_size,
        "mtime": _iso_mtime(resolved),
        "mime": media_type,
        "media_type": media_type,
        "content_class": content_class,
        "source_url": meta.get("source_url") or meta.get("original_url") or meta.get("selected_original_url"),
        "archive_url": meta.get("archive_url"),
        "raw_sha256": raw_sha,
        "final_sha256": final_sha,
        "preview_category": classify_preview(resolved, media_type, content_class),
        "renderer": renderer_for(resolved, media_type, content_class, display_path),
        "schema_hint": schema_hint_for(display_path),
        "warnings": warnings,
        "_file_path": resolved,
    }


def _raw_root(run_dir: Path) -> Path:
    frozen = load_frozen_config(run_dir)
    paths = frozen.get("paths") if isinstance(frozen.get("paths"), dict) else {}
    source = frozen.get("source_config") if isinstance(frozen.get("source_config"), dict) else {}
    source_paths = source.get("paths") if isinstance(source.get("paths"), dict) else {}
    value = paths.get("raw_root") or source_paths.get("raw_root") or "raw/sha256"
    return Path(str(value)).resolve()


def _safe_raw_path(raw_root: Path, row: dict[str, Any]) -> Path | None:
    raw_path = row.get("raw_path")
    sha = row.get("raw_sha256")
    candidates: list[Path] = []
    if isinstance(raw_path, str) and raw_path:
        candidates.append(Path(raw_path))
    if isinstance(sha, str) and len(sha) >= 2:
        candidates.append(raw_root / sha[:2] / sha)
    root = raw_root.resolve()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
            if resolved != root and root not in resolved.parents:
                continue
        except OSError:
            continue
        if resolved.is_file():
            return resolved
    return None


def _collect_object_records(run_dir: Path) -> list[dict[str, Any]]:
    """Build a fresh, read-only object index from a run's current files."""

    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    site_rows = {str(row.get("output_path") or ""): row for row in _jsonl(run_dir / "manifests" / "site.manifest.jsonl") if row.get("output_path")}
    raw_root = _raw_root(run_dir)

    def add(record: dict[str, Any] | None) -> None:
        if not record:
            return
        key = (record["object_id"], str(record.get("_file_path")))
        if key in seen:
            return
        seen.add(key)
        records.append(record)

    for artifact in iter_artifacts(run_dir):
        try:
            path = safe_child(run_dir, artifact["path"])
        except (KeyError, ValueError):
            continue
        add(_record(run_dir, kind=artifact.get("kind", "artifact"), stage=artifact.get("stage", "artifact"), file_path=path, display_path=artifact.get("path", path.name), metadata=artifact))

    cdx_pages = run_dir / "cdx" / "pages"
    if cdx_pages.is_dir():
        for path in sorted(cdx_pages.rglob("*")):
            if path.is_file():
                rel = path.relative_to(run_dir).as_posix()
                add(_record(run_dir, kind="cdx-page", stage="inventory", file_path=path, display_path=rel))

    staging = run_dir / "staging" / "normalized-site"
    if staging.is_dir():
        for path in sorted(staging.rglob("*")):
            if not path.is_file():
                continue
            output_path = path.relative_to(staging).as_posix()
            rel = path.relative_to(run_dir).as_posix()
            add(_record(run_dir, kind="site", stage="normalize", file_path=path, display_path=rel, metadata=site_rows.get(output_path, {}), id_path=output_path))

    for row in _jsonl(run_dir / "manifests" / "download.results.jsonl"):
        path = _safe_raw_path(raw_root, row)
        if path is None:
            continue
        sha = str(row.get("raw_sha256") or "")
        display = f"raw/sha256/{sha[:12]}" if sha else "raw/sha256/object"
        add(_record(run_dir, kind="raw", stage="download", file_path=path, display_path=display, metadata=row, id_path=str(row.get("raw_sha256") or display)))

    records.sort(key=lambda item: (str(item.get("kind")), str(item.get("display_path")), str(item.get("object_id"))))
    return records


def build_object_records(run_dir: Path) -> list[dict[str, Any]]:
    return [_public(record) for record in _collect_object_records(run_dir)]


def resolve_object(run_dir: Path, object_id: str) -> dict[str, Any] | None:
    for record in build_object_records_with_paths(run_dir):
        if record.get("object_id") == object_id:
            return record
    return None


def build_object_records_with_paths(run_dir: Path) -> list[dict[str, Any]]:
    # Same as build_object_records, but retains the private _file_path for route handlers.
    return _collect_object_records(run_dir)


def public_object(record: dict[str, Any]) -> dict[str, Any]:
    return _public(record)
