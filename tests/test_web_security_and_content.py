from __future__ import annotations

def csrf(client) -> str:
    response = client.get("/")
    assert response.status_code == 200
    return client.cookies["archive_recovery_csrf"]


def test_global_headers_and_csrf_cookie(web_client):
    response = web_client.get("/api/status")
    assert response.status_code == 200
    assert response.headers["x-robots-tag"] == "noindex, noarchive"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "content-security-policy" in response.headers
    assert "archive_recovery_csrf" in response.cookies


def test_post_requires_csrf(web_client):
    response = web_client.post("/api/config/validate", json={"domain": "example.com"})
    assert response.status_code == 403


def test_post_accepts_csrf(web_client):
    token = csrf(web_client)
    response = web_client.post("/api/config/validate", json={"domain": "example.com", "csrf_token": token}, headers={"X-CSRF-Token": token})
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_cross_site_origin_blocked(web_client):
    token = csrf(web_client)
    response = web_client.post("/api/config/validate", json={"domain": "example.com"}, headers={"X-CSRF-Token": token, "Origin": "https://evil.example"})
    assert response.status_code == 403


def test_site_preview_and_source_do_not_execute_html(web_client):
    preview = web_client.get("/runs/run-1/preview")
    assert preview.status_code == 200
    assert "sandboxed" in preview.text.lower()
    site = web_client.get("/runs/run-1/site/")
    assert site.status_code == 200
    assert "sandbox" in site.headers["content-security-policy"]
    objects = web_client.get("/api/runs/run-1/objects?q=index.html").json()["objects"]
    html_object = next(obj for obj in objects if obj["display_path"].endswith("index.html"))
    source = web_client.get(f"/runs/run-1/content/{html_object['object_id']}/source")
    assert source.status_code == 200
    assert source.headers["content-type"].startswith("text/plain")
    assert "<script>" in source.text


def test_object_rows_json_and_hex(web_client):
    objects = web_client.get("/api/runs/run-1/objects?renderer=download-results").json()["objects"]
    object_id = objects[0]["object_id"]
    rows = web_client.get(f"/api/runs/run-1/objects/{object_id}/rows?limit=1").json()
    assert rows["count"] == 1
    assert "fetch_state" in rows["columns"]
    hex_response = web_client.get(f"/api/runs/run-1/objects/{object_id}/hex?length=4")
    assert hex_response.status_code == 200


def test_dependency_recovery_stage_order_and_readiness(sample_workspace):
    import json

    from archive_recovery.web.jobs import STAGES
    from archive_recovery.web.workflow import stage_readiness

    run = sample_workspace["run"]
    stages = list(STAGES)
    assert stages.index("dependencies") < stages.index("dependency-recovery") < stages.index("normalize")
    frozen = json.loads((run / "config" / "run-config.json").read_text(encoding="utf-8"))
    frozen["config_path"] = str(sample_workspace["root"] / "configs" / "example.toml")
    (run / "config" / "run-config.json").write_text(json.dumps(frozen), encoding="utf-8")
    (run / "manifests" / "inventory.raw.jsonl").write_text("{}\n", encoding="utf-8")
    readiness = stage_readiness(run, STAGES)
    assert "dependency-recovery" in readiness
    assert readiness["dependency-recovery"]["ready"] is False
    assert "missing-dependency-requests.jsonl" in "; ".join(readiness["dependency-recovery"]["reasons"])
    (run / "manifests" / "missing-dependency-requests.jsonl").write_text("{}\n", encoding="utf-8")
    readiness = stage_readiness(run, STAGES)
    assert readiness["dependency-recovery"]["ready"] is True
    assert "manifests/inventory.raw.jsonl" in readiness["dependency-recovery"]["outputs"]
    assert "cdx/dependency-pages/" in readiness["dependency-recovery"]["outputs"]
    assert "reports/dependency-recovery-report.md" in readiness["dependency-recovery"]["outputs"]


def test_dependency_recovery_api_start_reports_not_ready(web_client, sample_workspace):
    import json

    from archive_recovery.cli import InterviewConfig, render_toml

    token = csrf(web_client)
    run = sample_workspace["run"]
    config_path = sample_workspace["root"] / "configs" / "example.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(render_toml(InterviewConfig(domain="example.com", config_path=str(config_path), runs_root=str(sample_workspace["runs"]), raw_root=str(sample_workspace["raw"]), data_dir=str(sample_workspace["root"] / "data"), recovered_root=str(sample_workspace["root"] / "recovered"))), encoding="utf-8")
    frozen = json.loads((run / "config" / "run-config.json").read_text(encoding="utf-8"))
    frozen["config_path"] = str(config_path)
    (run / "config" / "run-config.json").write_text(json.dumps(frozen), encoding="utf-8")
    (run / "manifests" / "inventory.raw.jsonl").write_text("{}\n", encoding="utf-8")

    response = web_client.post("/api/runs/run-1/stages/dependency-recovery", json={"csrf_token": token}, headers={"X-CSRF-Token": token})
    assert response.status_code == 409
    assert "missing-dependency-requests.jsonl" in response.text


def test_dependency_recovery_api_start_runs_stage(web_client, sample_workspace, monkeypatch):
    import json
    import time
    from urllib.parse import parse_qs, urlsplit

    from archive_recovery.cli import InterviewConfig, render_toml
    from archive_recovery.jsonl import read_jsonl

    root = sample_workspace["root"]
    run = sample_workspace["run"]
    config_path = root / "configs" / "example.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(render_toml(InterviewConfig(domain="example.com", aliases=[], path_prefix="/", cdx_filters=["statuscode:200"], cdx_limit=1000, config_path=str(config_path), runs_root=str(sample_workspace["runs"]), raw_root=str(sample_workspace["raw"]), data_dir=str(root / "data"), recovered_root=str(root / "recovered"))), encoding="utf-8")
    frozen = json.loads((run / "config" / "run-config.json").read_text(encoding="utf-8"))
    frozen["config_path"] = str(config_path)
    (run / "config" / "run-config.json").write_text(json.dumps(frozen), encoding="utf-8")
    inventory = run / "manifests" / "inventory.raw.jsonl"
    missing = run / "manifests" / "missing-dependency-requests.jsonl"
    inventory.write_text("", encoding="utf-8")
    missing.write_text(json.dumps({"request_id": "dep_css", "scope": "first-party", "original_url": "https://example.com/assets/app.css", "normalized_url": "https://example.com/assets/app.css", "target_mime_guess": "css", "high_value": True}) + "\n", encoding="utf-8")
    fetched_urls: list[str] = []

    def fake_fetch(url: str, *, timeout: int = 60) -> bytes:
        fetched_urls.append(url)
        requested = parse_qs(urlsplit(url).query)["url"][0]
        rows = [["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]]
        if requested == "https://example.com/assets/app.css":
            rows.append(["com,example)/assets/app.css", "20200102000000", "https://example.com/assets/app.css", "text/css", "200", "CSS", "42"])
        return json.dumps(rows).encode("utf-8")

    monkeypatch.setattr("archive_recovery.pipeline.inventory.fetch", fake_fetch)
    token = csrf(web_client)
    response = web_client.post("/api/runs/run-1/stages/dependency-recovery", json={"csrf_token": token}, headers={"X-CSRF-Token": token, "Accept": "application/json"})
    assert response.status_code == 202
    assert response.json()["stage"] == "dependency-recovery"

    status = {}
    for _ in range(50):
        status = web_client.get("/api/runs/run-1/status").json()
        if status.get("state") == "succeeded":
            break
        time.sleep(0.1)
    assert status["stage"] == "dependency-recovery"
    assert status["state"] == "succeeded"
    assert status["result"]["records_appended"] == 1
    assert status["result"]["report_path"].endswith("reports/dependency-recovery-report.md")

    rows = list(read_jsonl(inventory))
    assert any(row.get("dependency_request_id") == "dep_css" and row.get("original_url") == "https://example.com/assets/app.css" for row in rows)
    assert (run / "reports" / "dependency-recovery-report.md").is_file()
    assert list((run / "cdx" / "dependency-pages").glob("dep_css-q*.json"))
    assert fetched_urls

    events = web_client.get("/api/runs/run-1/events").json()["events"]
    assert any(event.get("event_type") == "stage_succeeded" and event.get("payload", {}).get("stage") == "dependency-recovery" for event in events)
    stages = web_client.get("/api/runs/run-1/stages").json()["stages"]
    assert stages["dependency-recovery"]["completed"] is True
