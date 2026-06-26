from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def sample_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    monkeypatch.chdir(tmp_path)
    runs = tmp_path / "runs"
    run = runs / "run-1"
    raw = tmp_path / "raw" / "sha256"
    for child in (run / "config", run / "manifests", run / "reports", run / "logs", run / "ops", run / "staging" / "normalized-site", raw):
        child.mkdir(parents=True, exist_ok=True)
    html = run / "staging" / "normalized-site" / "index.html"
    html.write_text("<html><script>alert(1)</script><h1>Hello</h1></html>", encoding="utf-8")
    image = run / "staging" / "normalized-site" / "image.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    blob_sha = "a" * 64
    blob = raw / blob_sha[:2] / blob_sha
    blob.parent.mkdir(parents=True, exist_ok=True)
    blob.write_bytes(b"hello archived bytes")
    (run / "config" / "run-config.json").write_text(
        json.dumps({"run_id": "run-1", "scope": {"domain": "example.com"}, "target_mode": "latest-good", "paths": {"raw_root": str(raw)}, "source_config": {"paths": {"raw_root": str(raw)}}}),
        encoding="utf-8",
    )
    (run / "manifests" / "site.manifest.jsonl").write_text(json.dumps({"output_path": "index.html", "content_class": "html", "response_content_type": "text/html", "source_url": "https://example.com/"}) + "\n", encoding="utf-8")
    (run / "manifests" / "download.results.jsonl").write_text(json.dumps({"job_id": "j1", "fetch_state": "succeeded", "raw_sha256": blob_sha, "raw_path": str(blob), "response_content_type": "text/html", "original_url": "https://example.com/"}) + "\n", encoding="utf-8")
    (run / "manifests" / "dependency-graph.jsonl").write_text(json.dumps({"resolution_state": "externalized", "resolved_url": "https://cdn.example.net/a.js"}) + "\n", encoding="utf-8")
    (run / "reports" / "validation-report.md").write_text("# Validation\n\nOK\n", encoding="utf-8")
    (run / "reports" / "external-links.json").write_text(json.dumps({"external_links": [{"source": "index.html", "context": "script", "attribute": "src", "url": "https://cdn.example.net/a.js"}]}), encoding="utf-8")
    (run / "logs" / "events.jsonl").write_text(json.dumps({"created_at": "now", "level": "info", "event_type": "test", "message": "ready", "payload": {}}) + "\n", encoding="utf-8")
    return {"root": tmp_path, "runs": runs, "run": run, "raw": raw}


@pytest.fixture()
def web_client(sample_workspace: dict[str, Path]):
    from starlette.testclient import TestClient

    from archive_recovery.web import create_app

    return TestClient(create_app(runs_root=sample_workspace["runs"]))


def csrf(client) -> str:
    response = client.get("/")
    assert response.status_code == 200
    return client.cookies["archive_recovery_csrf"]
