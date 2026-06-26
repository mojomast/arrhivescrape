from __future__ import annotations

from pathlib import Path

import pytest

from archive_recovery.web.fs import safe_child, safe_run_dir
from archive_recovery.web.object_index import build_object_records, public_object, resolve_object


def test_object_records_include_renderer_and_hide_private_paths(sample_workspace):
    records = build_object_records(sample_workspace["run"])
    assert any(record["renderer"] == "download-results" for record in records)
    assert any(record["preview_category"] == "source" and record["display_path"].endswith("index.html") for record in records)
    assert all("_file_path" not in record for record in records)


def test_resolve_object_retains_private_path_then_public_removes_it(sample_workspace):
    record = build_object_records(sample_workspace["run"])[0]
    resolved = resolve_object(sample_workspace["run"], record["object_id"])
    assert resolved is not None
    assert "_file_path" in resolved
    assert "_file_path" not in public_object(resolved)


def test_safe_child_rejects_escape(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(ValueError):
        safe_child(root, "../outside")


def test_safe_run_dir_rejects_bad_ids(sample_workspace):
    for value in ("", ".", "..", "a/b", "a\\b"):
        with pytest.raises(ValueError):
            safe_run_dir(sample_workspace["runs"], value)
