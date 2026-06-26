from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from archive_recovery.cli import InterviewConfig, render_toml
from archive_recovery.config import load_config
from archive_recovery.context import create_run_context
from archive_recovery.jsonl import read_jsonl, write_jsonl
from archive_recovery.pipeline.dependencies import make_graph_and_missing
from archive_recovery.pipeline.inventory import dependency_query_urls, run_dependency_recovery
from archive_recovery.pipeline.selection import run_selection


def make_context(tmp_path: Path):
    config_path = tmp_path / "example.toml"
    config_path.write_text(render_toml(InterviewConfig(domain="www.example.com", aliases=["example.com"], path_prefix="/blog", cdx_min_interval_seconds=0, config_path=str(config_path), runs_root=str(tmp_path / "runs"), raw_root=str(tmp_path / "raw"), data_dir=str(tmp_path / "data"), recovered_root=str(tmp_path / "recovered"))), encoding="utf-8")
    config = load_config(config_path)
    context = create_run_context(config, "run-1")
    context.ensure_dirs()
    return context


def test_dependencies_emit_missing_first_party_requests_only(tmp_path: Path):
    context = make_context(tmp_path)
    raw = tmp_path / "page.html"
    raw.write_text('<link href="/blog/assets/app.css" rel="stylesheet"><img src="/blog/images/logo.png"><script src="https://cdn.example.net/lib.js"></script>', encoding="utf-8")
    selections = [{"selection_id": "sel_page", "selected_original_url": "https://www.example.com/blog/", "normalized_url": "https://www.example.com/blog/", "identity_url": "https://www.example.com/blog/", "url_identity": "page", "mime_class": "html"}]
    downloads = [{"job_id": "sel_page", "original_url": "https://www.example.com/blog/", "fetch_state": "succeeded", "validation_state": "valid", "raw_path": str(raw), "response_content_type": "text/html", "raw_sha256": "abc"}]
    graph, missing, parsed, errors = make_graph_and_missing(context, selections, downloads)
    assert parsed == 1
    assert errors == 0
    assert {row["scope"] for row in graph} == {"first-party", "external"}
    assert {row["target_mime_guess"] for row in missing} == {"css", "image"}
    assert all(row["scope"] == "first-party" for row in missing)
    assert all(row["requested_stage"] == "inventory.dependencies" for row in missing)
    assert all(row["reason"] == "first-party-static-reference-not-selected" for row in missing)
    assert all(row["request_id"].startswith("dep_") for row in missing)
    assert all(row["high_value"] is True for row in missing)
    assert not any("cdn.example.net" in row["original_url"] for row in missing)


def test_dependency_recovery_appends_inventory_and_selection_picks_it_up(tmp_path: Path, monkeypatch):
    context = make_context(tmp_path)
    inventory = context.run_dir / "manifests" / "inventory.raw.jsonl"
    missing = context.run_dir / "manifests" / "missing-dependency-requests.jsonl"
    write_jsonl(inventory, [{"urlkey": "com,example,www)/blog/", "timestamp": "20200101000000", "original": "https://www.example.com/blog/", "mimetype": "text/html", "statuscode": "200", "digest": "HTML", "length": "100"}])
    write_jsonl(missing, [{"request_id": "dep_css", "scope": "first-party", "original_url": "https://www.example.com/blog/assets/app.css", "normalized_url": "https://www.example.com/blog/assets/app.css", "target_mime_guess": "css", "high_value": True}])

    def fake_fetch(url: str, *, timeout: int = 60) -> bytes:
        assert "matchType=exact" in url
        requested = parse_qs(urlsplit(url).query)["url"][0]
        if requested != "https://www.example.com/blog/assets/app.css":
            return json.dumps([
                ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"],
            ]).encode("utf-8")
        return json.dumps([
            ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"],
            ["com,example,www)/blog/assets/app.css", "20200102000000", "https://www.example.com/blog/assets/app.css", "text/css", "200", "CSS", "42"],
        ]).encode("utf-8")

    monkeypatch.setattr("archive_recovery.pipeline.inventory.fetch", fake_fetch)
    result = run_dependency_recovery(context)
    assert result.requests_considered == 1
    assert result.queries_issued == len(dependency_query_urls("https://www.example.com/blog/assets/app.css", context))
    assert result.records_appended == 1
    rows = list(read_jsonl(inventory))
    dependency = next(row for row in rows if row.get("dependency_request_id") == "dep_css")
    assert "dependency-recovery" in dependency["tags"]

    selection = run_selection(context)
    selected = list(read_jsonl(selection.selection_path))
    assert any(row["selected_original_url"] == "https://www.example.com/blog/assets/app.css" and row["mime_class"] == "css" for row in selected)


def test_dependency_recovery_queries_canonical_exact_variants(tmp_path: Path, monkeypatch):
    context = make_context(tmp_path)
    inventory = context.run_dir / "manifests" / "inventory.raw.jsonl"
    missing = context.run_dir / "manifests" / "missing-dependency-requests.jsonl"
    write_jsonl(missing, [{"request_id": "dep_css", "scope": "first-party", "original_url": "https://www.example.com/blog/assets/app.css", "normalized_url": "https://www.example.com/blog/assets/app.css", "target_mime_guess": "css", "high_value": True}])
    queried: list[str] = []

    def fake_fetch(url: str, *, timeout: int = 60) -> bytes:
        requested = parse_qs(urlsplit(url).query)["url"][0]
        queried.append(requested)
        rows = [["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]]
        if requested == "http://www.example.com/blog/assets/app.css":
            rows.append(["com,example,www)/blog/assets/app.css", "20200102000000", "http://www.example.com/blog/assets/app.css", "text/css", "200", "CSS", "42"])
        return json.dumps(rows).encode("utf-8")

    monkeypatch.setattr("archive_recovery.pipeline.inventory.fetch", fake_fetch)
    result = run_dependency_recovery(context)
    assert "http://www.example.com/blog/assets/app.css" in queried
    assert result.records_appended == 1
    assert any(row.get("original_url") == "http://www.example.com/blog/assets/app.css" for row in read_jsonl(inventory))


def test_dependency_recovery_is_idempotent_and_skips_duplicate_rows(tmp_path: Path, monkeypatch):
    context = make_context(tmp_path)
    inventory = context.run_dir / "manifests" / "inventory.raw.jsonl"
    missing = context.run_dir / "manifests" / "missing-dependency-requests.jsonl"
    write_jsonl(missing, [
        {"request_id": "dep_css", "scope": "first-party", "original_url": "https://www.example.com/blog/assets/app.css", "normalized_url": "https://www.example.com/blog/assets/app.css", "target_mime_guess": "css", "high_value": True},
        {"request_id": "dep_css_dup", "scope": "first-party", "original_url": "http://www.example.com/blog/assets/app.css", "normalized_url": "http://www.example.com/blog/assets/app.css", "target_mime_guess": "css", "high_value": False},
    ])
    fetches: list[str] = []

    def fake_fetch(url: str, *, timeout: int = 60) -> bytes:
        fetches.append(url)
        requested = parse_qs(urlsplit(url).query)["url"][0]
        rows = [["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]]
        if requested == "https://www.example.com/blog/assets/app.css":
            rows.extend([
                ["com,example,www)/blog/assets/app.css", "20200102000000", "https://www.example.com/blog/assets/app.css", "text/css", "200", "CSS", "42"],
                ["com,example,www)/blog/assets/app.css", "20200102000000", "https://www.example.com/blog/assets/app.css", "text/css", "200", "CSS", "42"],
            ])
        return json.dumps(rows).encode("utf-8")

    monkeypatch.setattr("archive_recovery.pipeline.inventory.fetch", fake_fetch)
    result = run_dependency_recovery(context)
    assert result.requests_considered == 1
    assert result.records_found == 2
    assert result.records_appended == 1
    rows = list(read_jsonl(inventory))
    assert len([row for row in rows if row.get("dependency_request_id") == "dep_css"]) == 1
    report = (context.run_dir / "reports" / "dependency-recovery-report.md").read_text(encoding="utf-8")
    assert "- duplicate_inventory_row: 1" in report

    fetches.clear()
    second = run_dependency_recovery(context)
    assert second.queries_issued == 0
    assert second.records_appended == 0
    assert not fetches
    assert len(list(read_jsonl(inventory))) == len(rows)


def test_dependency_recovery_resumes_from_saved_resume_key_and_clears_state(tmp_path: Path, monkeypatch):
    context = make_context(tmp_path)
    missing = context.run_dir / "manifests" / "missing-dependency-requests.jsonl"
    write_jsonl(missing, [{"request_id": "dep_css", "scope": "first-party", "original_url": "https://www.example.com/blog/assets/app.css", "normalized_url": "https://www.example.com/blog/assets/app.css", "target_mime_guess": "css", "high_value": True}])
    state_path = context.run_dir / "ops" / "dependency-recovery-state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"completed_requests": [], "resume_keys": {"dep_css": "resume-token"}}), encoding="utf-8")
    pages_dir = context.run_dir / "cdx" / "dependency-pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (pages_dir / "dep_css-q01-00001.json").write_text("[]", encoding="utf-8")
    requested_urls: list[str] = []

    def fake_fetch(url: str, *, timeout: int = 60) -> bytes:
        requested_urls.append(url)
        return json.dumps([["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]]).encode("utf-8")

    monkeypatch.setattr("archive_recovery.pipeline.inventory.fetch", fake_fetch)
    result = run_dependency_recovery(context)
    assert result.queries_issued == len(dependency_query_urls("https://www.example.com/blog/assets/app.css", context))
    assert "resumeKey=resume-token" in requested_urls[0]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["completed_requests"] == ["dep_css"]
    assert "dep_css" not in state["resume_keys"]
    assert (pages_dir / "dep_css-q01-00002.json").exists()
