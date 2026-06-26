from __future__ import annotations

import contextlib
import json
import threading
import traceback
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable

from archive_recovery.config import ConfigError, load_config
from archive_recovery.context import create_run_context
from archive_recovery.pipeline.captures_browser import run_captures_browser
from archive_recovery.pipeline.dependencies import run_dependencies
from archive_recovery.pipeline.download import run_download
from archive_recovery.pipeline.inventory import run_inventory
from archive_recovery.pipeline.normalization import run_normalize
from archive_recovery.pipeline.selection import run_selection
from archive_recovery.pipeline.validation import run_validate

from .fs import config_path_for_run, safe_run_dir, utc_now
from .workflow import ensure_runs_root_matches, stage_readiness


StageFunc = Callable[..., Any]


STAGES: dict[str, StageFunc] = {
    "inventory": run_inventory,
    "select": run_selection,
    "download": run_download,
    "dependencies": run_dependencies,
    "normalize": run_normalize,
    "validate": run_validate,
    "captures-browser": run_captures_browser,
}


def _option_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").lower() in {"1", "true", "yes", "on"}


class JobManager:
    """Tiny in-process background runner for local operator use."""

    def __init__(self, *, runs_root: Path, default_config: str | Path | None = None):
        self.runs_root = runs_root
        self.default_config = str(default_config) if default_config else None
        self._lock = threading.Lock()
        self._active: dict[str, threading.Thread] = {}

    def start(self, run_id: str, stage: str, *, config_path: str | Path | None = None, options: dict[str, Any] | None = None) -> dict[str, Any]:
        if stage not in STAGES:
            raise ValueError(f"unknown stage: {stage}")
        run_dir = safe_run_dir(self.runs_root, run_id)
        actual_config = str(config_path or config_path_for_run(run_dir) or self.default_config or "")
        if not actual_config:
            raise ConfigError("config path is required for this run")
        config = load_config(actual_config)
        ensure_runs_root_matches(config, self.runs_root)
        readiness = stage_readiness(run_dir, STAGES)
        stage_state = readiness.get(stage, {})
        if not stage_state.get("ready", False):
            reasons = stage_state.get("reasons") or ["stage requirements are not satisfied"]
            raise RuntimeError(f"stage {stage} is not ready: {'; '.join(reasons)}")
        lock_path = run_dir / "ops" / "stage-lock.json"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_payload = {"run_id": run_id, "stage": stage, "created_at": utc_now(), "config_path": actual_config}
        with self._lock:
            existing = self._active.get(run_id)
            if existing and existing.is_alive():
                raise RuntimeError(f"another stage is already running for run: {run_id}")
            try:
                with lock_path.open("x", encoding="utf-8") as handle:
                    handle.write(json.dumps(lock_payload, indent=2, sort_keys=True) + "\n")
            except FileExistsError as exc:
                raise RuntimeError(f"stage lock exists for run: {run_id} ({lock_path})") from exc
            thread = threading.Thread(target=self._run_stage, args=(run_id, stage, actual_config, options or {}, lock_path), name=f"{run_id}:{stage}", daemon=True)
            self._active[run_id] = thread
            try:
                thread.start()
            except Exception:
                lock_path.unlink(missing_ok=True)
                raise
        return {"run_id": run_id, "stage": stage, "state": "queued", "config_path": actual_config}

    def _run_stage(self, run_id: str, stage: str, config_path: str, options: dict[str, Any], lock_path: Path) -> None:
        run_dir = safe_run_dir(self.runs_root, run_id)
        (run_dir / "logs").mkdir(parents=True, exist_ok=True)
        (run_dir / "ops").mkdir(parents=True, exist_ok=True)
        log_path = run_dir / "logs" / f"{stage}.log"
        self._write_status(run_dir, stage=stage, state="running", started_at=utc_now(), config_path=config_path, run_id=run_id)
        self._event(run_dir, "info", "stage_started", f"Started {stage}", {"stage": stage})
        try:
            with log_path.open("a", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                config = load_config(config_path)
                context = create_run_context(config, run_id)
                context.ensure_dirs()
                if not context.run_config_path.exists():
                    context.write_frozen_config()
                result = STAGES[stage](context, **self._stage_kwargs(stage, options))
            payload = self._result_payload(result)
            self._write_status(run_dir, stage=stage, state="succeeded", finished_at=utc_now(), config_path=config_path, run_id=run_id, result=payload)
            self._event(run_dir, "info", "stage_succeeded", f"Finished {stage}", {"stage": stage, "result": payload})
        except Exception as exc:  # noqa: BLE001 - persist failure for the operator UI.
            with log_path.open("a", encoding="utf-8") as log:
                log.write("\n")
                traceback.print_exc(file=log)
            self._write_status(run_dir, stage=stage, state="failed", finished_at=utc_now(), config_path=config_path, run_id=run_id, error=str(exc))
            self._event(run_dir, "error", "stage_failed", f"Failed {stage}: {exc}", {"stage": stage, "error": str(exc)})
        finally:
            lock_path.unlink(missing_ok=True)

    def _stage_kwargs(self, stage: str, options: dict[str, Any]) -> dict[str, Any]:
        # Keep the web runner intentionally conservative: expose only simple
        # defaults plus inventory force/resume controls used during iteration.
        if stage == "inventory":
            return {"force": _option_bool(options.get("force")), "resume_key": options.get("resume_key") or None}
        return {}

    def _write_status(self, run_dir: Path, **status: Any) -> None:
        status.setdefault("updated_at", utc_now())
        path = run_dir / "ops" / "status.json"
        path.write_text(json.dumps(status, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    def _event(self, run_dir: Path, level: str, event_type: str, message: str, payload: dict[str, Any] | None = None) -> None:
        event = {"created_at": utc_now(), "level": level, "event_type": event_type, "message": message, "payload": payload or {}}
        with (run_dir / "logs" / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")

    def _result_payload(self, result: Any) -> Any:
        if is_dataclass(result):
            return asdict(result)
        if isinstance(result, (str, int, float, bool)) or result is None:
            return result
        if isinstance(result, Path):
            return str(result)
        return str(result)
