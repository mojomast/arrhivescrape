from __future__ import annotations

import asyncio
import html
import json
import secrets
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from archive_recovery.config import ConfigError, load_config

from .fs import ARTIFACT_DIRS, iter_artifacts, list_runs, read_events, run_status, safe_child, safe_run_dir
from .jobs import JobManager, STAGES
from .object_index import build_object_records, public_object, resolve_object
from .workflow import defaults_payload, initialize_run_from_config, interview_from_payload, list_target_configs, render_and_validate, request_payload, run_details, stage_readiness, write_config_from_payload

PACKAGE_DIR = Path(__file__).resolve().parent


CSRF_COOKIE = "archive_recovery_csrf"
AUTH_COOKIE = "archive_recovery_auth"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def create_app(*, runs_root: str | Path = "runs", config_path: str | Path | None = None, auth_token: str | None = None, allowed_hosts: list[str] | None = None) -> Any:
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
        context.setdefault("csrf_token", getattr(request.state, "csrf_token", ""))
        context.setdefault("auth_enabled", bool(auth_token))
        return templates.TemplateResponse(request, name, context)

    def bool_payload(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value or "").lower() in {"1", "true", "yes", "on"}

    def host_name(host_header: str) -> str:
        if host_header.startswith("[") and "]" in host_header:
            return host_header[1:].split("]", 1)[0].lower().rstrip(".")
        return host_header.rsplit(":", 1)[0].lower().rstrip(".")

    def host_port(host_header: str, scheme: str) -> tuple[str, int | None]:
        try:
            parsed = urlparse("//" + host_header)
            host = (parsed.hostname or "").lower().rstrip(".")
            port = parsed.port
        except ValueError:
            return host_name(host_header), None
        return host, port or (443 if scheme == "https" else 80)

    def first_header_value(value: str) -> str:
        return value.split(",", 1)[0].strip()

    host_allowlist = {"127.0.0.1", "localhost", "::1", "testserver"}
    for item in allowed_hosts or []:
        if item:
            host_allowlist.add(host_name(str(item)))

    def same_origin(request: Any, value: str) -> bool:
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            return False
        origin_host = (parsed.hostname or "").lower().rstrip(".")
        origin_port = parsed.port or (443 if parsed.scheme == "https" else 80)
        candidates = [(request.url.scheme, *host_port(request.headers.get("host", ""), request.url.scheme))]
        forwarded_host = first_header_value(request.headers.get("x-forwarded-host", ""))
        forwarded_proto = first_header_value(request.headers.get("x-forwarded-proto", "")) or request.url.scheme
        if forwarded_host and forwarded_proto in {"http", "https"} and host_name(forwarded_host) in host_allowlist:
            candidates.append((forwarded_proto, *host_port(forwarded_host, forwarded_proto)))
        for scheme, candidate_host, candidate_port in candidates:
            if parsed.scheme == scheme and origin_host == candidate_host and origin_port == candidate_port:
                return True
        if parsed.scheme in {"http", "https"} and origin_host in host_allowlist:
            return True
        return False

    def bearer_authenticated(request: Any) -> bool:
        if not auth_token:
            return False
        header = request.headers.get("authorization", "")
        return header == f"Bearer {auth_token}"

    def request_authenticated(request: Any) -> bool:
        if not auth_token:
            return True
        return bearer_authenticated(request) or request.cookies.get(AUTH_COOKIE) == auth_token or request.query_params.get("token") == auth_token

    def csrf_valid(request: Any, payload: dict[str, Any] | None = None) -> bool:
        if bearer_authenticated(request):
            return True
        cookie = request.cookies.get(CSRF_COOKIE)
        provided = request.headers.get("x-csrf-token") or (payload or {}).get("csrf_token")
        return bool(cookie and provided and secrets.compare_digest(str(cookie), str(provided)))

    def parse_limit_offset(request: Any, *, default: int = 100, maximum: int = 1000) -> tuple[int, int]:
        try:
            limit = int(request.query_params.get("limit", str(default)))
            offset = int(request.query_params.get("offset", "0"))
        except ValueError:
            limit, offset = default, 0
        return max(1, min(limit, maximum)), max(0, offset)

    def filtered_objects(request: Any, run_dir: Path) -> tuple[list[dict[str, Any]], int, int, int]:
        objects = build_object_records(run_dir)
        q = request.query_params.get("q", "").strip().lower()
        for field in ("kind", "stage", "preview", "renderer"):
            wanted = request.query_params.get(field, "").strip().lower()
            if wanted:
                key = "preview_category" if field == "preview" else field
                objects = [obj for obj in objects if str(obj.get(key, "")).lower() == wanted]
        if q:
            objects = [obj for obj in objects if q in " ".join(str(obj.get(key, "")) for key in ("object_id", "display_path", "kind", "stage", "renderer", "media_type", "source_url")).lower()]
        total = len(objects)
        limit, offset = parse_limit_offset(request)
        return objects[offset : offset + limit], total, limit, offset

    def object_file(request: Any) -> tuple[Path | None, dict[str, Any] | None, Response | None]:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        record = resolve_object(run_dir, request.path_params["object_id"])
        if record is None:
            return None, None, PlainTextResponse("object not found", status_code=404)
        path = record.get("_file_path")
        if not isinstance(path, Path) or not path.is_file():
            return None, record, PlainTextResponse("object file not found", status_code=404)
        return path, record, None

    def read_jsonl_rows(path: Path, *, limit: int, offset: int) -> tuple[list[dict[str, Any]], list[str], int]:
        rows: list[dict[str, Any]] = []
        columns: list[str] = []
        total = 0
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(value, dict):
                    continue
                if total < 200:
                    for key in value:
                        if key not in columns:
                            columns.append(key)
                if total >= offset and len(rows) < limit:
                    rows.append(value)
                total += 1
        return rows, columns, total

    def rows_for_object(path: Path, record: dict[str, Any], *, limit: int, offset: int) -> dict[str, Any]:
        renderer = str(record.get("renderer") or "")
        if renderer == "external-links":
            data = json.loads(path.read_text(encoding="utf-8"))
            values = data.get("external_links", []) if isinstance(data, dict) else []
            rows = [item for item in values if isinstance(item, dict)]
            columns = ["source", "context", "attribute", "url"]
            return {"columns": columns, "rows": rows[offset : offset + limit], "count": len(rows), "limit": limit, "offset": offset}
        rows, columns, total = read_jsonl_rows(path, limit=limit, offset=offset)
        return {"columns": columns, "rows": rows, "count": total, "limit": limit, "offset": offset}

    def markdown_html(path: Path, *, max_bytes: int = 262144) -> str:
        text = path.read_text(encoding="utf-8", errors="replace")[:max_bytes]
        parts: list[str] = []
        in_code = False
        for line in text.splitlines():
            escaped = html.escape(line)
            if line.strip().startswith("```"):
                parts.append("</code></pre>" if in_code else "<pre><code>")
                in_code = not in_code
            elif in_code:
                parts.append(escaped)
            elif line.startswith("#"):
                level = min(len(line) - len(line.lstrip("#")), 6)
                content = html.escape(line[level:].strip())
                parts.append(f"<h{level}>{content}</h{level}>")
            elif line.strip():
                parts.append(f"<p>{escaped}</p>")
            else:
                parts.append("")
        if in_code:
            parts.append("</code></pre>")
        return "\n".join(parts)

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
            if not csrf_valid(request, payload):
                return JSONResponse({"error": "CSRF token required"}, status_code=403)
            if payload.get("config_path"):
                config = load_config(payload["config_path"])
                return JSONResponse({"valid": True, "config": {"path": str(config.path), "domain": config.domain, "target_mode": config.target_mode, "runs_root": str(config.runs_root)}})
            toml = render_and_validate(interview_from_payload(payload))
            return JSONResponse({"valid": True, "toml": toml})
        except Exception as exc:  # noqa: BLE001 - validation endpoint returns form errors.
            return JSONResponse({"valid": False, "error": str(exc)}, status_code=400)

    async def api_create_config(request: Any) -> JSONResponse:
        try:
            payload = await request_payload(request)
            if not csrf_valid(request, payload):
                return JSONResponse({"error": "CSRF token required"}, status_code=403)
            result = write_config_from_payload(payload)
        except Exception as exc:  # noqa: BLE001 - surface browser form errors.
            return JSONResponse({"error": str(exc)}, status_code=409)
        return JSONResponse(result, status_code=201)

    async def api_create_run(request: Any) -> JSONResponse:
        try:
            payload = await request_payload(request)
            if not csrf_valid(request, payload):
                return JSONResponse({"error": "CSRF token required"}, status_code=403)
            result = initialize_run_from_config(payload.get("config_path") or config_path or "", root, run_id=payload.get("run_id") or None, force=bool_payload(payload.get("force")))
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
            payload = await request_payload(request)
            if not csrf_valid(request, payload):
                return PlainTextResponse("CSRF token required", status_code=403)
            result = write_config_from_payload(payload)
        except Exception as exc:  # noqa: BLE001 - return form-friendly errors.
            return PlainTextResponse(str(exc), status_code=409)
        return RedirectResponse(f"/targets?created={result['path']}", status_code=303)

    async def create_run_form(request: Any) -> Response:
        try:
            payload = await request_payload(request)
            if not csrf_valid(request, payload):
                return PlainTextResponse("CSRF token required", status_code=403)
            result = initialize_run_from_config(payload.get("config_path") or config_path or "", root, run_id=payload.get("run_id") or None, force=bool_payload(payload.get("force")))
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
        objects, total, limit, offset = filtered_objects(request, run_dir)
        return JSONResponse({"run_id": run_dir.name, "count": total, "limit": limit, "offset": offset, "objects": objects})

    async def api_object_detail(request: Any) -> JSONResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        record = resolve_object(run_dir, request.path_params["object_id"])
        if record is None:
            return JSONResponse({"error": "object not found"}, status_code=404)
        return JSONResponse(public_object(record))

    async def object_library(request: Any) -> HTMLResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        objects, total, limit, offset = filtered_objects(request, run_dir)
        all_objects = build_object_records(run_dir)
        return render(request, "artifacts.html", {"request": request, "run_id": run_dir.name, "objects": objects, "all_objects": all_objects, "count": total, "limit": limit, "offset": offset})

    async def object_view(request: Any) -> Response:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        record = resolve_object(run_dir, request.path_params["object_id"])
        if record is None:
            return PlainTextResponse("object not found", status_code=404)
        public = public_object(record)
        path = record.get("_file_path")
        render_data: dict[str, Any] = {}
        if isinstance(path, Path) and path.is_file():
            renderer = str(public.get("renderer") or "")
            if renderer in {"jsonl", "events", "download-results", "dependency-graph", "site-manifest", "inventory", "selection", "canonical-inventory", "missing-dependencies", "normalization-results"}:
                render_data = rows_for_object(path, public, limit=100, offset=0)
            elif renderer == "external-links":
                render_data = rows_for_object(path, public, limit=250, offset=0)
            elif renderer == "markdown":
                render_data = {"html": markdown_html(path)}
            elif renderer == "json":
                render_data = {"api_json": f"/api/runs/{run_dir.name}/objects/{public['object_id']}/json"}
            elif renderer in {"pdf-metadata", "binary"}:
                render_data = {"api_hex": f"/api/runs/{run_dir.name}/objects/{public['object_id']}/hex"}
        return render(request, "artifact_view.html", {"request": request, "run_id": run_dir.name, "object": public, "render_data": render_data})

    async def api_object_rows(request: Any) -> JSONResponse:
        path, record, error = object_file(request)
        if error:
            return JSONResponse({"error": error.body.decode()}, status_code=error.status_code)
        assert path is not None and record is not None
        limit, offset = parse_limit_offset(request, default=100, maximum=1000)
        try:
            return JSONResponse(rows_for_object(path, record, limit=limit, offset=offset))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=415)

    async def api_object_json(request: Any) -> JSONResponse:
        path, record, error = object_file(request)
        if error:
            return JSONResponse({"error": error.body.decode()}, status_code=error.status_code)
        assert path is not None and record is not None
        if path.stat().st_size > 5 * 1024 * 1024:
            return JSONResponse({"error": "JSON object is too large for inline parsing"}, status_code=413)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=415)
        return JSONResponse({"object": public_object(record), "json": data})

    async def api_object_hex(request: Any) -> JSONResponse:
        path, record, error = object_file(request)
        if error:
            return JSONResponse({"error": error.body.decode()}, status_code=error.status_code)
        assert path is not None and record is not None
        try:
            offset = max(0, int(request.query_params.get("offset", "0")))
            length = max(1, min(int(request.query_params.get("length", "4096")), 65536))
        except ValueError:
            offset, length = 0, 4096
        with path.open("rb") as handle:
            handle.seek(offset)
            chunk = handle.read(length)
        return JSONResponse({"object": public_object(record), "offset": offset, "length": len(chunk), "hex": chunk.hex(), "ascii": "".join(chr(byte) if 32 <= byte < 127 else "." for byte in chunk)})

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
        if not csrf_valid(request, payload):
            return PlainTextResponse("CSRF token required", status_code=403)
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

    async def site_preview(request: Any) -> HTMLResponse:
        run_dir = safe_run_dir(root, request.path_params["run_id"])
        site = run_dir / "staging" / "normalized-site"
        return render(request, "site_preview.html", {"request": request, "run_id": run_dir.name, "site_ready": site.is_dir() and (site / "index.html").is_file()})

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
        return FileResponse(path, headers={"X-Robots-Tag": "noindex, noarchive", "X-Content-Type-Options": "nosniff", "Content-Security-Policy": "default-src 'none'; sandbox; script-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'; img-src 'self' data:; media-src 'self'; style-src 'unsafe-inline';"})

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
        Route("/api/runs/{run_id}/objects/{object_id}/rows", api_object_rows),
        Route("/api/runs/{run_id}/objects/{object_id}/json", api_object_json),
        Route("/api/runs/{run_id}/objects/{object_id}/hex", api_object_hex),
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
        Route("/runs/{run_id}/preview", site_preview),
        Route("/runs/{run_id}/site/", site_file),
        Route("/runs/{run_id}/site/{path:path}", site_file),
        Mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static"),
    ]
    app = Starlette(debug=False, routes=routes)

    @app.middleware("http")
    async def security_and_headers(request: Any, call_next: Any) -> Response:
        host = host_name(request.headers.get("host", ""))
        if host and host not in host_allowlist:
            return PlainTextResponse("Host not allowed", status_code=400)
        request.state.csrf_token = request.cookies.get(CSRF_COOKIE) or secrets.token_urlsafe(32)
        if not request_authenticated(request):
            return PlainTextResponse("Authentication required", status_code=401, headers={"WWW-Authenticate": "Bearer"})
        if request.method in UNSAFE_METHODS:
            fetch_site = request.headers.get("sec-fetch-site", "").lower()
            if fetch_site in {"cross-site", "none"}:
                return PlainTextResponse("Cross-site unsafe request blocked", status_code=403)
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            if origin and not same_origin(request, origin):
                return PlainTextResponse("Origin not allowed", status_code=403)
            if not origin and referer and not same_origin(request, referer):
                return PlainTextResponse("Referer not allowed", status_code=403)
        response = await call_next(request)
        if request.query_params.get("token") == auth_token and auth_token:
            response.set_cookie(AUTH_COOKIE, auth_token, httponly=True, samesite="strict", secure=request.url.scheme == "https")
        if request.cookies.get(CSRF_COOKIE) != request.state.csrf_token:
            response.set_cookie(CSRF_COOKIE, request.state.csrf_token, httponly=True, samesite="strict", secure=request.url.scheme == "https")
        response.headers.setdefault("X-Robots-Tag", "noindex, noarchive")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if not response.headers.get("content-security-policy"):
            if request.url.path.startswith(("/runs/",)) and "/content/" in request.url.path:
                response.headers.setdefault("Content-Security-Policy", "default-src 'none'; sandbox")
            else:
                response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        return response

    return app
