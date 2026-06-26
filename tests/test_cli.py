from __future__ import annotations

import pytest

from pathlib import Path

from archive_recovery.cli import clean_host, clean_path_prefix, default_alias_for, main


def test_top_level_help_lists_commands(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    for command in ("new", "init", "validate-config", "inventory", "select", "download", "dependencies", "dependency-recovery", "normalize", "validate", "captures-browser", "serve-site", "web"):
        assert command in output


@pytest.mark.parametrize("command", ["new", "init", "validate-config", "inventory", "select", "download", "dependencies", "dependency-recovery", "normalize", "validate", "captures-browser", "serve-site", "web"])
def test_subcommand_help_exits_zero(command):
    with pytest.raises(SystemExit) as exc:
        main([command, "--help"])
    assert exc.value.code == 0


def test_clean_host_normalizes_url():
    assert clean_host("https://Example.COM/path") == "example.com"


def test_path_prefix_and_www_alias_defaults():
    assert clean_path_prefix("blog") == "/blog"
    assert clean_path_prefix("/blog/") == "/blog"
    assert default_alias_for("www.example.com") == "example.com"
    assert default_alias_for("example.com") == "www.example.com"


def test_web_rejects_nonlocal_without_auth():
    with pytest.raises(SystemExit) as exc:
        main(["web", "--host", "0.0.0.0", "--allow-nonlocal"])
    assert "requires --auth-token" in str(exc.value)


def test_serve_site_serves_normalized_site_directly(sample_workspace, monkeypatch, capsys):
    captured = {}

    class FakeServer:
        def __init__(self, address, handler):
            captured["address"] = address
            captured["handler"] = handler
            captured["closed"] = False

        def serve_forever(self):
            captured["served"] = True
            raise KeyboardInterrupt

        def server_close(self):
            captured["closed"] = True

    monkeypatch.setattr("archive_recovery.cli.http.server.ThreadingHTTPServer", FakeServer)
    assert main(["serve-site", "--runs-root", str(sample_workspace["runs"]), "--run-id", "run-1", "--host", "127.0.0.1", "--port", "18082"]) == 0
    output = capsys.readouterr().out
    assert captured["address"] == ("127.0.0.1", 18082)
    assert captured["served"] is True
    assert captured["closed"] is True
    assert "Serving" in output
    assert "URL: http://127.0.0.1:18082/" in output


def test_serve_site_rejects_missing_staging_site(tmp_path: Path):
    with pytest.raises(SystemExit) as exc:
        main(["serve-site", "--runs-root", str(tmp_path), "--run-id", "missing"])
    assert "staging site not found" in str(exc.value)
