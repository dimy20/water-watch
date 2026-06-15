import pytest

from scripts.backup import _check_cmd


def test_check_cmd_existe_no_hace_nada(monkeypatch):
    monkeypatch.setattr("scripts.backup.shutil.which", lambda name: "/usr/bin/" + name)

    _check_cmd("pg_dump")


def test_check_cmd_no_existe_termina_el_programa(monkeypatch, capsys):
    monkeypatch.setattr("scripts.backup.shutil.which", lambda name: None)

    with pytest.raises(SystemExit) as exc_info:
        _check_cmd("pg_dump")

    assert exc_info.value.code == 1
    assert "pg_dump" in capsys.readouterr().out
