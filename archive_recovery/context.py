from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import RecoveryConfig


RUN_SUBDIRS = (
    "config",
    "cdx/pages",
    "manifests",
    "logs",
    "reports",
    "ops",
    "staging/normalized-site",
)


@dataclass(frozen=True)
class RunContext:
    """Filesystem locations for one recovery run."""

    config: RecoveryConfig
    run_id: str
    run_dir: Path

    @property
    def config_dir(self) -> Path:
        return self.run_dir / "config"

    @property
    def run_config_path(self) -> Path:
        return self.config_dir / "run-config.json"

    @property
    def staging_site(self) -> Path:
        return self.run_dir / "staging" / "normalized-site"

    @property
    def release_site(self) -> Path:
        return self.config.recovered_root / "releases" / self.run_id / "site"

    @property
    def promoted_site(self) -> Path:
        promoted = self.config.paths.get("promoted_site")
        return Path(promoted) if promoted else self.config.recovered_root / "site"

    def ensure_dirs(self) -> None:
        for child in RUN_SUBDIRS:
            (self.run_dir / child).mkdir(parents=True, exist_ok=True)
        self.config.raw_root.mkdir(parents=True, exist_ok=True)
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

    def frozen_config(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "config_path": str(self.config.path),
            "config_version": self.config.config_version,
            "scope": {
                "domain": self.config.domain,
                "canonical_host": self.config.canonical_host,
                "alias_hosts": list(self.config.alias_hosts),
                "path_prefix": self.config.path_prefix,
            },
            "target_mode": self.config.target_mode,
            "paths": {
                "run_dir": str(self.run_dir),
                "staging_site": str(self.staging_site),
                "release_site": str(self.release_site),
                "promoted_site": str(self.promoted_site),
                "sqlite_path": str(self.config.sqlite_path),
                "raw_root": str(self.config.raw_root),
            },
            "source_config": self.config.raw,
        }

    def write_frozen_config(self, *, force: bool = False) -> None:
        if self.run_config_path.exists() and not force:
            raise FileExistsError(f"run config already exists: {self.run_config_path}")
        self.run_config_path.write_text(json.dumps(self.frozen_config(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_run_id(target_mode: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{target_mode}"


def create_run_context(config: RecoveryConfig, run_id: str | None = None) -> RunContext:
    actual_run_id = run_id or default_run_id(config.target_mode)
    return RunContext(config=config, run_id=actual_run_id, run_dir=config.runs_root / actual_run_id)


def initialize_run(config: RecoveryConfig, run_id: str | None = None, *, force: bool = False) -> RunContext:
    context = create_run_context(config, run_id)
    context.ensure_dirs()
    context.write_frozen_config(force=force)
    return context
