from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_DIRS = ("config", "manifests", "reports", "logs", "ops")
MANIFEST_NAMES = {
    "inventory.raw.jsonl": "inventory",
    "selection.pruned.jsonl": "selection",
    "inventory.canonical.jsonl": "selection",
    "download.results.jsonl": "download",
    "dependency-graph.jsonl": "dependencies",
    "missing-dependency-requests.jsonl": "dependencies",
    "normalization.results.jsonl": "normalize",
    "site.manifest.jsonl": "normalize",
}
REPORT_NAMES = {
    "selection-report.md": "selection",
    "download-report.md": "download",
    "dependency-report.md": "dependencies",
    "normalization-report.md": "normalize",
    "mime-audit.md": "normalize",
    "validation-report.md": "validate",
    "external-links.json": "validate",
}


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    run_dir: Path
    status: dict[str, Any]
    artifact_count: int
    updated_at: str
    domain: str
    target_mode: str
    publication_intent: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_child(root: Path, user_path: str | None = None) -> Path:
    """Resolve a user path under ``root`` and reject traversal/symlink escapes."""

    base = root.resolve()
    candidate = (base / (user_path or "")).resolve()
    if candidate != base and base not in candidate.parents:
        raise ValueError("path escapes allowed root")
    return candidate


def safe_run_dir(runs_root: Path, run_id: str) -> Path:
    if not run_id or "/" in run_id or "\\" in run_id or run_id in {".", ".."}:
        raise ValueError("invalid run id")
    run_dir = safe_child(runs_root, run_id)
    if not run_dir.is_dir():
        raise FileNotFoundError(run_id)
    return run_dir


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def count_jsonl(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def load_frozen_config(run_dir: Path) -> dict[str, Any]:
    value = load_json(run_dir / "config" / "run-config.json", {})
    return value if isinstance(value, dict) else {}


def read_events(run_dir: Path, *, limit: int = 200) -> list[dict[str, Any]]:
    events_path = run_dir / "logs" / "events.jsonl"
    events: list[dict[str, Any]] = []
    try:
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                value = {"level": "warning", "message": line, "created_at": utc_now()}
            if isinstance(value, dict):
                events.append(value)
    except FileNotFoundError:
        pass
    return events[-limit:]


def run_status(run_dir: Path) -> dict[str, Any]:
    status = load_json(run_dir / "ops" / "status.json", {})
    if not isinstance(status, dict):
        status = {}
    status.setdefault("run_id", run_dir.name)
    status.setdefault("state", "idle")
    status.setdefault("events", len(read_events(run_dir, limit=10_000)))
    status.setdefault("metrics", run_metrics(run_dir))
    return status


def run_metrics(run_dir: Path) -> dict[str, Any]:
    manifests = run_dir / "manifests"
    reports = run_dir / "reports"
    staging = run_dir / "staging" / "normalized-site"
    metrics: dict[str, Any] = {
        "inventory_records": count_jsonl(manifests / "inventory.raw.jsonl"),
        "selected_captures": count_jsonl(manifests / "selection.pruned.jsonl"),
        "download_results": count_jsonl(manifests / "download.results.jsonl"),
        "dependencies": count_jsonl(manifests / "dependency-graph.jsonl"),
        "missing_dependencies": count_jsonl(manifests / "missing-dependency-requests.jsonl"),
        "normalized_files": count_jsonl(manifests / "site.manifest.jsonl"),
        "reports": len([path for path in reports.rglob("*") if path.is_file()]) if reports.is_dir() else 0,
        "staging_files": len([path for path in staging.rglob("*") if path.is_file()]) if staging.is_dir() else 0,
    }
    external_links = load_json(reports / "external-links.json", {})
    if isinstance(external_links, dict) and isinstance(external_links.get("external_links"), list):
        metrics["external_links"] = len(external_links["external_links"])
    return metrics


def iter_artifacts(run_dir: Path) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for dirname in ARTIFACT_DIRS:
        root = run_dir / dirname
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(run_dir).as_posix()
            stat = path.stat()
            artifacts.append(
                {
                    "path": rel,
                    "name": path.name,
                    "size": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
                    "kind": dirname,
                    "stage": MANIFEST_NAMES.get(path.name) or REPORT_NAMES.get(path.name) or dirname,
                }
            )
    return artifacts


def list_runs(runs_root: Path) -> list[RunSummary]:
    if not runs_root.exists():
        return []
    runs: list[RunSummary] = []
    for run_dir in sorted((p for p in runs_root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True):
        artifacts = iter_artifacts(run_dir)
        updated = datetime.fromtimestamp(run_dir.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
        frozen = load_frozen_config(run_dir)
        scope = frozen.get("scope") if isinstance(frozen.get("scope"), dict) else {}
        source_config = frozen.get("source_config") if isinstance(frozen.get("source_config"), dict) else {}
        privacy = source_config.get("privacy") if isinstance(source_config.get("privacy"), dict) else {}
        domain = scope.get("domain") if isinstance(scope.get("domain"), str) else ""
        target_mode = frozen.get("target_mode") if isinstance(frozen.get("target_mode"), str) else ""
        publication = privacy.get("publication_intent") if isinstance(privacy.get("publication_intent"), str) else "private-local"
        runs.append(RunSummary(run_dir.name, run_dir, run_status(run_dir), len(artifacts), updated, domain, target_mode, publication))
    return runs


def config_path_for_run(run_dir: Path) -> str | None:
    frozen = load_frozen_config(run_dir)
    if isinstance(frozen, dict):
        value = frozen.get("config_path")
        if isinstance(value, str) and value:
            return value
    return None
