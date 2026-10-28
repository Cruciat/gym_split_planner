"""Comandi di servizio ``python -m gym_split_planner``."""

import json
from pathlib import Path

import pytest

from gym_split_planner.__main__ import main
from gym_split_planner.config import get_settings


@pytest.fixture(autouse=True)
def database_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GSP_DATABASE_URL", f"sqlite:///{tmp_path / 'db.sqlite'}")
    get_settings.cache_clear()


def test_migrate_command(capsys: pytest.CaptureFixture[str]) -> None:
    main(["migrate"])

    assert "Database alla revisione 0002" in capsys.readouterr().out


def test_seed_command_loads_once(capsys: pytest.CaptureFixture[str]) -> None:
    main(["migrate"])
    main(["seed"])
    main(["seed"])

    out = capsys.readouterr().out
    assert "Dati iniziali caricati: 81 esercizi, 40 famiglie, 6 split" in out
    assert "Database già popolato" in out


def test_seed_command_can_be_skipped(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GSP_SKIP_SEED", "1")
    get_settings.cache_clear()
    main(["migrate"])
    main(["seed"])

    assert "Dati iniziali saltati" in capsys.readouterr().out


def test_openapi_command_prints_schema(capsys: pytest.CaptureFixture[str]) -> None:
    main(["openapi"])

    schema = json.loads(capsys.readouterr().out)
    assert schema["info"]["title"] == "Gym Split Planner"
    assert "/api/health" in schema["paths"]
