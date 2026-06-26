from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HOST_RE = re.compile(
    r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])$",
    re.I,
)


class ConfigError(ValueError):
    """Raised when a recovery TOML file is missing required values."""


@dataclass(frozen=True)
class RecoveryConfig:
    """Validated recovery configuration loaded from TOML.

    The original TOML content remains available in ``raw`` so future pipeline
    stages can consume sections that are not yet modeled by this foundation.
    """

    path: Path
    raw: dict[str, Any]
    config_version: int
    project_name: str
    domain: str
    canonical_host: str
    alias_hosts: tuple[str, ...]
    target_mode: str
    paths: dict[str, str]

    @property
    def runs_root(self) -> Path:
        return Path(self.paths.get("runs_root", "runs"))

    @property
    def data_dir(self) -> Path:
        return Path(self.paths.get("data_dir", "data"))

    @property
    def sqlite_path(self) -> Path:
        return Path(self.paths.get("sqlite_path", self.data_dir / f"{self.domain}.sqlite3"))

    @property
    def raw_root(self) -> Path:
        return Path(self.paths.get("raw_root", "raw/sha256"))

    @property
    def recovered_root(self) -> Path:
        return Path(self.paths.get("recovered_root", f"recovered/{self.domain}"))


def load_config(path: str | Path) -> RecoveryConfig:
    """Load and validate a recovery TOML config using stdlib ``tomllib``."""

    config_path = Path(path)
    try:
        with config_path.open("rb") as handle:
            raw = tomllib.load(handle)
    except FileNotFoundError as exc:
        raise ConfigError(f"config not found: {config_path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {config_path}: {exc}") from exc

    project = _table(raw, "project")
    scope = _table(raw, "scope")
    target = _table(raw, "target")
    paths = _table(raw, "paths")

    config_version = _int(project, "config_version")
    if config_version != 1:
        raise ConfigError(f"unsupported project.config_version: {config_version}")

    domain = _host(scope, "domain")
    canonical_host = _host(scope, "canonical_host")
    alias_hosts = tuple(_host_value(item, "scope.alias_hosts") for item in _str_list(scope, "alias_hosts", default=[]))
    target_mode = _str(target, "mode")

    string_paths: dict[str, str] = {}
    for key, value in paths.items():
        if not isinstance(value, str) or not value:
            raise ConfigError(f"paths.{key} must be a non-empty string")
        string_paths[key] = value
    for required_path in ("data_dir", "sqlite_path", "raw_root", "runs_root", "recovered_root"):
        if required_path not in string_paths:
            raise ConfigError(f"missing paths.{required_path}")

    return RecoveryConfig(
        path=config_path,
        raw=raw,
        config_version=config_version,
        project_name=_str(project, "name"),
        domain=domain,
        canonical_host=canonical_host,
        alias_hosts=alias_hosts,
        target_mode=target_mode,
        paths=string_paths,
    )


def _table(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"missing [{key}] table")
    return value


def _str(table: dict[str, Any], key: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{key} must be a non-empty string")
    return value


def _int(table: dict[str, Any], key: str) -> int:
    value = table.get(key)
    if not isinstance(value, int):
        raise ConfigError(f"{key} must be an integer")
    return value


def _str_list(table: dict[str, Any], key: str, default: list[str] | None = None) -> list[str]:
    value = table.get(key, default)
    if value is None:
        raise ConfigError(f"{key} must be a list of strings")
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ConfigError(f"{key} must be a list of strings")
    return value


def _host(table: dict[str, Any], key: str) -> str:
    return _host_value(_str(table, key), key)


def _host_value(value: str, key: str) -> str:
    cleaned = value.strip().lower().rstrip(".")
    if not HOST_RE.match(cleaned):
        raise ConfigError(f"{key} must be a valid host, got {value!r}")
    return cleaned
