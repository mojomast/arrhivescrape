from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from archive_recovery.config import ConfigError, load_config

from .fs import ARTIFACT_DIRS, iter_artifacts, list_runs, read_events, run_status, safe_child, safe_run_dir
from .jobs import JobManager, STAGES
from .object_index import build_object_records, public_object, resolve_object
from .workflow import defaults_payload, initialize_run_from_config, interview_from_payload, list_target_configs, render_and_validate, request_payload, run_details, stage_readiness, write_config_from_payload

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
        runs = list_runs(root)
        run_cards = [{"summary": run, "stages": stage_readiness(run.run_dir, STAGES)} for run in runs]
        return render(request, "runs.html", {"request": request, "runs": runs, "run_cards": run_cards, "targets": list_target_configs()})

    async def targets_page(request: Any) -> HTMLResponse:
        targets = list_target_configs()
        return render(request, "targets.html", {"request": request, "targets": targets})

    async def target_new_page(request: Any) -> HTMLResponse:
        return render(request, "target_new.html", {"request": request})

    async def run_page(request: Any) -> HTMLResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        run_id = run_dir.name
        return render(
            request,
            "run.html",
            {"request": request, "run_id": run_id, "status": run_status(run_dir), "artifacts": iter_artifacts(run_dir), "object_count": len(build_object_records(run_dir)), "events": read_events(run_dir), "stages": stage_readiness(run_dir, STAGES)},
        )

    async def api_status(request: Any) -> JSONResponse:
        return JSONResponse({"runs_root": str(root), "runs": [run.__dict__ | {"run_dir": str(run.run_dir)} for run in list_runs(root)]})

    async def api_run_status(request: Any) -> JSONResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        return JSONResponse(run_status(run_dir))

    async def api_configs(request: Any) -> JSONResponse:
        return JSONResponse({"configs": list_target_configs()})

    async def api_config_defaults(request: Any) -> JSONResponse:
        return JSONResponse(defaults_payload())

    async def api_config_validate(request: Any) -> JSONResponse:
        try:
            payload = await request_payload(request)
            if payload.get("config_path"):
                config = load_config(payload["config_path"])
                return JSONResponse({"valid": True, "config": {"path": str(config.path), "domain": config.domain, "target_mode": config.target_mode, "runs_root": str(config.runs_root)}})
            toml = render_and_validate(interview_from_payload(payload))
            return JSONResponse({"valid": True, "toml": toml})
        except Exception as exc:  # noqa: BLE001 - validation endpoint returns form errors.
            return JSONResponse({"valid": False, "error": str(exc)}, status_code=400)

    async def api_create_config(request: Any) -> JSONResponse:
        try:
            result = write_config_from_payload(await request_payload(request))
        except Exception as exc:  # noqa: BLE001 - surface browser form errors.
            return JSONResponse({"error": str(exc)}, status_code=409)
        return JSONResponse(result, status_code=201)

    async def api_create_run(request: Any) -> JSONResponse:
        try:
            payload = await request_payload(request)
            result = initialize_run_from_config(payload.get("config_path") or config_path or "", root, run_id=payload.get("run_id") or None, force=str(payload.get("force", "")).lower() in {"1", "true", "yes", "on"})
        except Exception as exc:  # noqa: BLE001 - surface browser form errors.
            return JSONResponse({"error": str(exc)}, status_code=409)
        return JSONResponse(result, status_code=201)

    async def api_run_detail(request: Any) -> JSONResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        detail = run_details(run_dir, run_status(run_dir), iter_artifacts(run_dir), STAGES)
        detail["object_count"] = len(build_object_records(run_dir))
        return JSONResponse(detail)

    async def api_run_stages(request: Any) -> JSONResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        return JSONResponse({"run_id": run_dir.name, "stages": stage_readiness(run_dir, STAGES)})

    async def create_target_form(request: Any) -> Response:
        try:
            result = write_config_from_payload(await request_payload(request))
        except Exception as exc:  # noqa: BLE001 - return form-friendly errors.
            return PlainTextResponse(str(exc), status_code=409)
        return RedirectResponse(f"/targets?created={result['path']}", status_code=303)

    async def create_run_form(request: Any) -> Response:
        try:
            payload = await request_payload(request)
            result = initialize_run_from_config(payload.get("config_path") or config_path or "", root, run_id=payload.get("run_id") or None, force=str(payload.get("force", "")).lower() in {"1", "true", "yes", "on"})
        except Exception as exc:  # noqa: BLE001 - return form-friendly errors.
            return PlainTextResponse(str(exc), status_code=409)
        return RedirectResponse(f"/runs/{result['run_id']}", status_code=303)

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

    async def api_objects(request: Any) -> JSONResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        objects = build_object_records(run_dir)
        return JSONResponse({"run_id": run_dir.name, "count": len(objects), "objects": objects})

    async def api_object_detail(request: Any) -> JSONResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        record = resolve_object(run_dir, request.path_params["object_id"])
        if record is None:
            return JSONResponse({"error": "object not found"}, status_code=404)
        return JSONResponse(public_object(record))

    async def object_library(request: Any) -> HTMLResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        objects = build_object_records(run_dir)
        return render(request, "artifacts.html", {"request": request, "run_id": run_dir.name, "objects": objects, "count": len(objects)})

    async def object_view(request: Any) -> Response:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        record = resolve_object(run_dir, request.path_params["object_id"])
        if record is None:
            return PlainTextResponse("object not found", status_code=404)
        return render(request, "artifact_view.html", {"request": request, "run_id": run_dir.name, "object": public_object(record)})

    def object_response(request: Any, *, mode: str) -> Response:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        record = resolve_object(run_dir, request.path_params["object_id"])
        if record is None:
            return PlainTextResponse("object not found", status_code=404)
        path = record.get("_file_path")
        if not isinstance(path, Path) or not path.is_file():
            return PlainTextResponse("object file not found", status_code=404)
        media_type = str(record.get("media_type") or "application/octet-stream")
        preview = str(record.get("preview_category") or "none")
        strict_headers = {"Content-Security-Policy": "default-src 'none'; sandbox", "X-Content-Type-Options": "nosniff"}
        if mode == "source":
            if preview != "source":
                return PlainTextResponse("source preview not available", status_code=415, headers=strict_headers)
            return FileResponse(path, media_type="text/plain; charset=utf-8", headers=strict_headers)
        if mode == "preview":
            if preview not in {"image", "audio", "video"}:
                return PlainTextResponse("inline preview not available", status_code=415, headers=strict_headers)
            return FileResponse(path, media_type=media_type, headers=strict_headers)
        if mode == "download":
            return FileResponse(path, media_type="application/octet-stream", filename=path.name)
        return FileResponse(path, media_type="application/octet-stream", filename=path.name)

    async def object_source(request: Any) -> Response:
        return object_response(request, mode="source")

    async def object_preview(request: Any) -> Response:
        return object_response(request, mode="preview")

    async def object_download(request: Any) -> Response:
        return object_response(request, mode="download")

    async def object_bytes(request: Any) -> Response:
        return object_response(request, mode="bytes")

    async def start_stage(request: Any) -> Response:
        payload: dict[str, Any] = {}
        if request.headers.get("content-type", ""):
            payload = await request_payload(request)
        try:
            result = jobs.start(request.path_params["run_id"], request.path_params["stage"], config_path=payload.get("config_path"), options=payload)
        except (ConfigError, FileNotFoundError, RuntimeError, ValueError) as exc:
            return PlainTextResponse(str(exc), status_code=409)
        accept = request.headers.get("accept", "")
        if "text/html" in accept and "application/json" not in accept:
            return RedirectResponse(f"/runs/{request.path_params['run_id']}", status_code=303)
        return JSONResponse(result, status_code=202)

    async def artifact_file(request: Any) -> Response:
        try:
            run_dir = safe_run_dir(root, request.path_params["run_id"])
            requested = request.path_params.get("path", "")
            if requested.split("/", 1)[0] not in ARTIFACT_DIRS:
                return PlainTextResponse("artifact path not allowed", status_code=403)
            path = safe_child(run_dir, requested)
        except ValueError as exc:
            return PlainTextResponse(str(exc), status_code=403)
        if not path.is_file():
            return PlainTextResponse("not found", status_code=404)
        for record in build_object_records(run_dir):
            if record.get("display_path") == requested:
                return RedirectResponse(f"/runs/{run_dir.name}/artifacts/view/{record['object_id']}", status_code=303)
        return FileResponse(path, media_type="application/octet-stream", filename=path.name)

    async def report_file(request: Any) -> Response:
        try:
            run_dir = safe_run_dir(root, request.path_params["run_id"])
            path = safe_child(run_dir / "reports", request.path_params.get("path", ""))
        except ValueError as exc:
            return PlainTextResponse(str(exc), status_code=403)
        if not path.is_file():
            return PlainTextResponse("not found", status_code=404)
        return FileResponse(path)

    async def site_file(request: Any) -> Response:
        try:
            run_dir = safe_run_dir(root, request.path_params["run_id"])
            site = run_dir / "staging" / "normalized-site"
            if not site.is_dir():
                return PlainTextResponse("staging site not found", status_code=404)
            requested = request.path_params.get("path", "") or "index.html"
            path = safe_child(site, requested)
            if path.is_dir():
                path = safe_child(path, "index.html")
        except ValueError as exc:
            return PlainTextResponse(str(exc), status_code=403)
        if not path.is_file():
            return PlainTextResponse("not found", status_code=404)
        return FileResponse(path, headers={"X-Robots-Tag": "noindex, noarchive", "X-Content-Type-Options": "nosniff", "Content-Security-Policy": "default-src 'none'; sandbox; img-src 'self' data:; media-src 'self'; style-src 'unsafe-inline';"})

    routes = [
        Route("/", dashboard),
        Route("/targets", targets_page),
        Route("/targets", create_target_form, methods=["POST"]),
        Route("/targets/new", target_new_page),
        Route("/runs", runs_page),
        Route("/runs", create_run_form, methods=["POST"]),
        Route("/runs/{run_id}", run_page),
        Route("/api/status", api_status),
        Route("/api/configs", api_configs),
        Route("/api/config/defaults", api_config_defaults),
        Route("/api/config/validate", api_config_validate, methods=["POST"]),
        Route("/api/configs", api_create_config, methods=["POST"]),
        Route("/api/runs", api_create_run, methods=["POST"]),
        Route("/api/runs/{run_id}", api_run_detail),
        Route("/api/runs/{run_id}/status", api_run_status),
        Route("/api/runs/{run_id}/stages", api_run_stages),
        Route("/api/runs/{run_id}/events", api_events),
        Route("/api/runs/{run_id}/events/stream", event_stream),
        Route("/api/runs/{run_id}/artifacts", api_artifacts),
        Route("/api/runs/{run_id}/objects", api_objects),
        Route("/api/runs/{run_id}/objects/{object_id}", api_object_detail),
        Route("/api/runs/{run_id}/objects/{object_id}/source", object_source),
        Route("/api/runs/{run_id}/objects/{object_id}/preview", object_preview),
        Route("/api/runs/{run_id}/objects/{object_id}/download", object_download),
        Route("/api/runs/{run_id}/objects/{object_id}/bytes", object_bytes),
        Route("/api/runs/{run_id}/stages/{stage}", start_stage, methods=["POST"]),
        Route("/runs/{run_id}/reports/{path:path}", report_file),
        Route("/runs/{run_id}/artifacts", object_library),
        Route("/runs/{run_id}/artifacts/view/{object_id}", object_view),
        Route("/runs/{run_id}/objects", object_library),
        Route("/runs/{run_id}/objects/{object_id}", object_view),
        Route("/runs/{run_id}/content/{object_id}/source", object_source),
        Route("/runs/{run_id}/content/{object_id}/preview", object_preview),
        Route("/runs/{run_id}/content/{object_id}/download", object_download),
        Route("/runs/{run_id}/content/{object_id}/bytes", object_bytes),
        Route("/runs/{run_id}/artifacts/{path:path}", artifact_file),
        Route("/runs/{run_id}/site/", site_file),
        Route("/runs/{run_id}/site/{path:path}", site_file),
        Mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static"),
    ]
    app = Starlette(debug=False, routes=routes)

    @app.middleware("http")
    async def noindex_headers(request: Any, call_next: Any) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Robots-Tag", "noindex, noarchive")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if not response.headers.get("content-security-policy"):
            if request.url.path.startswith(("/runs/",)) and "/content/" in request.url.path:
                response.headers.setdefault("Content-Security-Policy", "default-src 'none'; sandbox")
            else:
                response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        return response

    return app
