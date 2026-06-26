from __future__ import annotations

import pytest

from archive_recovery.cli import clean_host, main


def test_top_level_help_lists_commands(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    for command in ("new", "init", "validate-config", "inventory", "select", "download", "dependencies", "normalize", "validate", "captures-browser", "web"):
        assert command in output


@pytest.mark.parametrize("command", ["new", "init", "validate-config", "inventory", "select", "download", "dependencies", "normalize", "validate", "captures-browser", "web"])
def test_subcommand_help_exits_zero(command):
    with pytest.raises(SystemExit) as exc:
        main([command, "--help"])
    assert exc.value.code == 0


def test_clean_host_normalizes_url():
    assert clean_host("https://Example.COM/path") == "example.com"


def test_web_rejects_nonlocal_without_auth():
    with pytest.raises(SystemExit) as exc:
        main(["web", "--host", "0.0.0.0", "--allow-nonlocal"])
    assert "requires --auth-token" in str(exc.value)
