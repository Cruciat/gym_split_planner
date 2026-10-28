"""Comandi di servizio: ``python -m gym_split_planner <comando>``.

- ``migrate``: porta il database all'ultima revisione;
- ``seed``: carica i dati iniziali, solo se il database è vuoto e ``GSP_SKIP_SEED`` non è attivo;
- ``openapi``: stampa lo schema OpenAPI, usato per generare i tipi del frontend.
"""

import argparse
import json
import sys

from gym_split_planner.app import create_app
from gym_split_planner.config import get_settings
from gym_split_planner.db.engine import make_engine
from gym_split_planner.db.migrate import current_revision, upgrade_to_head
from gym_split_planner.db.seed.loader import seed_if_empty


def _migrate() -> None:
    engine = make_engine(get_settings().database_url)
    upgrade_to_head(engine)
    print(f"Database alla revisione {current_revision(engine)}")
    engine.dispose()


def _seed() -> None:
    settings = get_settings()
    if settings.skip_seed:
        print("Dati iniziali saltati (GSP_SKIP_SEED attivo)")
        return
    engine = make_engine(settings.database_url)
    report = seed_if_empty(engine)
    engine.dispose()
    if report is None:
        print("Database già popolato: dati iniziali non caricati")
    else:
        print(
            f"Dati iniziali caricati: {report.exercises} esercizi, "
            f"{report.families} famiglie, {report.splits} split"
        )


def _openapi() -> None:
    schema = create_app().openapi()
    json.dump(schema, sys.stdout, indent=2, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="gym_split_planner")
    parser.add_argument("command", choices=["migrate", "seed", "openapi"])
    args = parser.parse_args(argv)
    {"migrate": _migrate, "seed": _seed, "openapi": _openapi}[args.command]()


if __name__ == "__main__":
    main()
