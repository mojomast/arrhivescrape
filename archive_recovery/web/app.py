from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from archive_recovery.config import ConfigError, load_config

from .fs import ARTIFACT_DIRS, iter_artifacts, list_runs, read_events, run_status, safe_child, safe_run_dir
from .jobs import JobManager, STAGES

PACKAGE_DIR = Path(__file__).resolve().parent


def create_app(*, runs_root: str | Path = "runs", config_path: str | Path | None = None) -> Any:
    """Create the optional Starlette app.

    Starlette and Jinja2 are intentionally optional so the core CLI remains
    dependency-free. Install them (and an ASGI server such as uvicorn) to run
    this local operator UI.
    """

    try:
        from starlette.applications import Starlette
        from starlette.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response, StreamingResponse
        from starlette.routing import Mount, Route
        from starlette.staticfiles import StaticFiles
        from starlette.templating import Jinja2Templates
    except ImportError as exc:  # pragma: no cover - exercised only without optional deps.
        raise RuntimeError("archive_recovery.web requires optional dependencies: starlette jinja2") from exc

    root = Path(runs_root)
    jobs = JobManager(runs_root=root, default_config=config_path)
    templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")

    def render(request: Any, name: str, context: dict[str, Any]) -> HTMLResponse:
        return templates.TemplateResponse(request, name, context)

    async def dashboard(request: Any) -> HTMLResponse:
        runs = list_runs(root)
        return render(request, "dashboard.html", {"request": request, "runs": runs, "config_path": config_path, "runs_root": root})

    async def runs_page(request: Any) -> HTMLResponse:
        return render(request, "runs.html", {"request": request, "runs": list_runs(root)})

    async def targets_page(request: Any) -> HTMLResponse:
        targets: list[dict[str, Any]] = []
        for path in sorted(Path("configs").glob("*.toml")):
            try:
                config = load_config(path)
                targets.append({"path": path, "valid": True, "domain": config.domain, "aliases": config.alias_hosts, "target_mode": config.target_mode, "error": ""})
            except ConfigError as exc:
                targets.append({"path": path, "valid": False, "domain": path.stem, "aliases": (), "target_mode": "", "error": str(exc)})
        return render(request, "targets.html", {"request": request, "targets": targets})

    async def target_new_page(request: Any) -> HTMLResponse:
        return render(request, "target_new.html", {"request": request})

    async def run_page(request: Any) -> HTMLResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        run_id = run_dir.name
        return render(
            request,
            "run.html",
            {"request": request, "run_id": run_id, "status": run_status(run_dir), "artifacts": iter_artifacts(run_dir), "events": read_events(run_dir), "stages": STAGES},
        )

    async def api_status(request: Any) -> JSONResponse:
        return JSONResponse({"runs_root": str(root), "runs": [run.__dict__ | {"run_dir": str(run.run_dir)} for run in list_runs(root)]})

    async def api_run_status(request: Any) -> JSONResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        return JSONResponse(run_status(run_dir))

    async def api_events(request: Any) -> JSONResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        limit = int(request.query_params.get("limit", "200"))
        return JSONResponse({"events": read_events(run_dir, limit=max(1, min(limit, 2000)))})

    async def event_stream(request: Any) -> StreamingResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])

        async def stream() -> Any:
            sent = 0
            while True:
                events = read_events(run_dir, limit=2000)
                for event in events[sent:]:
                    yield f"event: progress\ndata: {json.dumps(event, default=str)}\n\n"
                sent = len(events)
                if await request.is_disconnected():
                    break
                await asyncio.sleep(1.5)

        return StreamingResponse(stream(), media_type="text/event-stream")

    async def api_artifacts(request: Any) -> JSONResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        return JSONResponse({"artifacts": iter_artifacts(run_dir)})

    async def start_stage(request: Any) -> Response:
        payload: dict[str, Any] = {}
        if request.headers.get("content-type", "").startswith("application/json"):
            payload = await request.json()
        try:
            result = jobs.start(request.path_params["run_id"], request.path_params["stage"], config_path=payload.get("config_path"), options=payload)
        except (ConfigError, FileNotFoundError, RuntimeError, ValueError) as exc:
            return PlainTextResponse(str(exc), status_code=409)
        accept = request.headers.get("accept", "")
        if "text/html" in accept and "application/json" not in accept:
            return RedirectResponse(f"/runs/{request.path_params['run_id']}", status_code=303)
        return JSONResponse(result, status_code=202)

    async def artifact_file(request: Any) -> Response:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        requested = request.path_params.get("path", "")
        if requested.split("/", 1)[0] not in ARTIFACT_DIRS:
            return PlainTextResponse("artifact path not allowed", status_code=403)
        path = safe_child(run_dir, requested)
        if not path.is_file():
            return PlainTextResponse("not found", status_code=404)
        return FileResponse(path)

    async def report_file(request: Any) -> Response:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        path = safe_child(run_dir / "reports", request.path_params.get("path", ""))
        if not path.is_file():
            return PlainTextResponse("not found", status_code=404)
        return FileResponse(path)

    async def site_file(request: Any) -> Response:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        site = run_dir / "staging" / "normalized-site"
        if not site.is_dir():
            return PlainTextResponse("staging site not found", status_code=404)
        requested = request.path_params.get("path", "") or "index.html"
        path = safe_child(site, requested)
        if path.is_dir():
            path = safe_child(path, "index.html")
        if not path.is_file():
            return PlainTextResponse("not found", status_code=404)
        return FileResponse(path)

    routes = [
        Route("/", dashboard),
        Route("/targets", targets_page),
        Route("/targets/new", target_new_page),
        Route("/runs", runs_page),
        Route("/runs/{run_id}", run_page),
        Route("/api/status", api_status),
        Route("/api/runs/{run_id}/status", api_run_status),
        Route("/api/runs/{run_id}/events", api_events),
        Route("/api/runs/{run_id}/events/stream", event_stream),
        Route("/api/runs/{run_id}/artifacts", api_artifacts),
        Route("/api/runs/{run_id}/stages/{stage}", start_stage, methods=["POST"]),
        Route("/runs/{run_id}/reports/{path:path}", report_file),
        Route("/runs/{run_id}/artifacts/{path:path}", artifact_file),
        Route("/runs/{run_id}/site/", site_file),
        Route("/runs/{run_id}/site/{path:path}", site_file),
        Mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static"),
    ]
    return Starlette(debug=False, routes=routes)
