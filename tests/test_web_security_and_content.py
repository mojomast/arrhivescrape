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
