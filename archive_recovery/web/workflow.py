from __future__ import annotations

import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from archive_recovery.cli import (
    PUBLICATION_POLICIES,
    SERVING_PREFERENCES,
    TARGET_MODES,
    THIRD_PARTY_MODES,
    InterviewConfig,
    clean_host,
    render_toml,
    split_hosts,
)
from archive_recovery.config import ConfigError, RecoveryConfig, load_config
from archive_recovery.context import initialize_run
from archive_recovery.state import init_db, register_run

from .fs import config_path_for_run, load_frozen_config, safe_child


CONFIGS_ROOT = Path("configs")


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "yes", "on"}


def _int(value: Any, default: int) -> int:
    if value in (None, ""):
        return default
    return int(value)


def _float(value: Any, default: float) -> float:
    if value in (None, ""):
        return default
    return float(value)


async def request_payload(request: Any) -> dict[str, Any]:
    """Parse JSON or browser form payloads without adding form dependencies."""

    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        value = await request.json()
        if not isinstance(value, dict):
            raise ValueError("JSON payload must be an object")
        return value
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def defaults_payload() -> dict[str, Any]:
    defaults = InterviewConfig(domain="example.com")
    return {
        "defaults": asdict(defaults),
        "target_modes": TARGET_MODES,
        "third_party_modes": THIRD_PARTY_MODES,
        "publication_policies": PUBLICATION_POLICIES,
        "serving_preferences": SERVING_PREFERENCES,
    }


def config_path_under_configs(domain: str, requested: str | None = None) -> Path:
    """Return a traversal-safe config path under configs/."""

    filename = requested or f"{domain}.toml"
    if not filename.endswith(".toml"):
        filename = f"{filename}.toml"
    if "/" in filename or "\\" in filename or filename in {".", ".."}:
        raise ValueError("config filename must be a simple .toml name")
    return safe_child(CONFIGS_ROOT, filename)


def interview_from_payload(payload: dict[str, Any]) -> InterviewConfig:
    domain = clean_host(str(payload.get("domain", "")))
    target_mode = str(payload.get("target_mode") or "latest-good")
    if target_mode not in TARGET_MODES:
        raise ValueError(f"target_mode must be one of: {', '.join(TARGET_MODES)}")
    third_party_mode = str(payload.get("third_party_mode") or "audit-only")
    if third_party_mode not in THIRD_PARTY_MODES:
        raise ValueError(f"third_party_mode must be one of: {', '.join(THIRD_PARTY_MODES)}")
    publication_policy = str(payload.get("publication_policy") or "private-tailnet")
    if publication_policy not in PUBLICATION_POLICIES:
        raise ValueError(f"publication_policy must be one of: {', '.join(PUBLICATION_POLICIES)}")
    serving_preference = str(payload.get("serving_preference") or "caddy-local")
    if serving_preference not in SERVING_PREFERENCES:
        raise ValueError(f"serving_preference must be one of: {', '.join(SERVING_PREFERENCES)}")
    recovered_root = str(payload.get("recovered_root") or f"recovered/{domain}")
    config_path = config_path_under_configs(domain, str(payload.get("config_name") or "")).as_posix()
    return InterviewConfig(
        domain=domain,
        aliases=split_hosts(str(payload.get("aliases") or f"www.{domain}")),
        target_mode=target_mode,
        target_date=str(payload.get("target_date") or ""),
        cdx_endpoint=str(payload.get("cdx_endpoint") or "https://web.archive.org/cdx/search/cdx"),
        cdx_filters=[item.strip() for item in str(payload.get("cdx_filters") or "statuscode:200").split(",") if item.strip()],
        cdx_limit=_int(payload.get("cdx_limit"), 1000),
        cdx_min_interval_seconds=_float(payload.get("cdx_min_interval_seconds"), 1.1),
        content_workers=_int(payload.get("content_workers"), 4),
        content_timeout_seconds=_int(payload.get("content_timeout_seconds"), 30),
        third_party_mode=third_party_mode,
        recover_third_party_hosts=split_hosts(str(payload.get("recover_third_party_hosts") or "")) if third_party_mode not in {"off", "audit-only"} else [],
        config_path=config_path,
        runs_root=str(payload.get("runs_root") or "runs"),
        raw_root=str(payload.get("raw_root") or "raw/sha256"),
        data_dir=str(payload.get("data_dir") or "data"),
        recovered_root=recovered_root,
        publication_policy=publication_policy,
        serving_preference=serving_preference,
        bind_host=str(payload.get("bind_host") or "127.0.0.1"),
        bind_port=_int(payload.get("bind_port"), 18080),
        public_hostname=str(payload.get("public_hostname") or ""),
    )


def render_and_validate(config: InterviewConfig) -> str:
    toml = render_toml(config)
    with tempfile.TemporaryDirectory(prefix="archive-recovery-config-") as temp_dir:
        path = Path(temp_dir) / "config.toml"
        path.write_text(toml, encoding="utf-8")
        load_config(path)
    return toml


def write_config_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    config = interview_from_payload(payload)
    toml = render_and_validate(config)
    path = Path(config.config_path)
    if path.exists() and not _bool(payload.get("force")):
        raise FileExistsError(f"config already exists: {path}; set force=true to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(toml, encoding="utf-8")
    loaded = load_config(path)
    return config_summary(path, loaded)


def config_summary(path: Path, config: RecoveryConfig | None = None, error: str = "") -> dict[str, Any]:
    if config is None and not error:
        config = load_config(path)
    return {
        "path": path.as_posix(),
        "valid": not error,
        "domain": config.domain if config else path.stem,
        "aliases": list(config.alias_hosts) if config else [],
        "target_mode": config.target_mode if config else "",
        "runs_root": str(config.runs_root) if config else "",
        "error": error,
    }


def list_target_configs() -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for path in sorted(CONFIGS_ROOT.glob("*.toml")):
        try:
            targets.append(config_summary(path))
        except ConfigError as exc:
            targets.append(config_summary(path, error=str(exc)))
    return targets


def ensure_runs_root_matches(config: RecoveryConfig, runs_root: Path) -> None:
    if config.runs_root.resolve() != runs_root.resolve():
        raise ConfigError(f"config paths.runs_root ({config.runs_root}) does not match web runs root ({runs_root})")


def initialize_run_from_config(config_path: str | Path, runs_root: Path, *, run_id: str | None = None, force: bool = False) -> dict[str, Any]:
    config = load_config(config_path)
    ensure_runs_root_matches(config, runs_root)
    context = initialize_run(config, run_id, force=force)
    init_db(config.sqlite_path)
    register_run(config.sqlite_path, run_id=context.run_id, config_path=str(config.path), run_dir=str(context.run_dir))
    return {"run_id": context.run_id, "run_dir": str(context.run_dir), "config_path": str(config.path), "run_config_path": str(context.run_config_path), "sqlite_path": str(config.sqlite_path)}


STAGE_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "inventory": (),
    "select": ("manifests/inventory.raw.jsonl",),
    "download": ("manifests/selection.pruned.jsonl",),
    "dependencies": ("manifests/selection.pruned.jsonl", "manifests/download.results.jsonl"),
    "normalize": ("manifests/selection.pruned.jsonl", "manifests/inventory.canonical.jsonl", "manifests/download.results.jsonl"),
    "validate": ("manifests/site.manifest.jsonl",),
    "captures-browser": ("manifests/inventory.raw.jsonl",),
}

STAGE_OUTPUTS: dict[str, tuple[str, ...]] = {
    "inventory": ("manifests/inventory.raw.jsonl",),
    "select": ("manifests/selection.pruned.jsonl", "manifests/inventory.canonical.jsonl"),
    "download": ("manifests/download.results.jsonl",),
    "dependencies": ("manifests/dependency-graph.jsonl", "manifests/missing-dependency-requests.jsonl"),
    "normalize": ("manifests/site.manifest.jsonl", "manifests/normalization.results.jsonl"),
    "validate": ("reports/validation-report.md", "reports/external-links.json"),
    "captures-browser": ("reports/captures-browser/index.html", "reports/captures-browser/captures.json"),
}


def stage_readiness(run_dir: Path, stages: Any) -> dict[str, dict[str, Any]]:
    lock_path = run_dir / "ops" / "stage-lock.json"
    frozen_config_path = config_path_for_run(run_dir)
    readiness: dict[str, dict[str, Any]] = {}
    for stage in stages:
        requirements = list(STAGE_REQUIREMENTS.get(stage, ()))
        outputs = list(STAGE_OUTPUTS.get(stage, ()))
        missing = [path for path in requirements if not (run_dir / path).exists()]
        completed = bool(outputs) and all((run_dir / path).exists() for path in outputs)
        reasons: list[str] = []
        if missing:
            reasons.append("missing requirements: " + ", ".join(missing))
        if lock_path.exists():
            reasons.append(f"stage lock exists: {lock_path}")
        if not frozen_config_path:
            reasons.append("run has no frozen config_path")
        ready = not lock_path.exists() and bool(frozen_config_path) and (stage == "inventory" or not missing)
        readiness[stage] = {"stage": stage, "requirements": requirements, "outputs": outputs, "completed": completed, "reasons": reasons, "ready": ready}
    return readiness


def run_details(run_dir: Path, status: dict[str, Any], artifacts: list[dict[str, Any]], stages: Any) -> dict[str, Any]:
    frozen = load_frozen_config(run_dir)
    return {"run_id": run_dir.name, "run_dir": str(run_dir), "status": status, "artifacts": artifacts, "frozen_config": frozen, "stages": stage_readiness(run_dir, stages)}
