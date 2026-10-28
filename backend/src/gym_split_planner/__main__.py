"""Comandi di servizio: ``python -m gym_split_planner <comando>``.

- ``migrate``: porta il database all'ultima revisione;
- ``openapi``: stampa lo schema OpenAPI, usato per generare i tipi del frontend.
"""

import argparse
import json
import sys

from gym_split_planner.app import create_app
from gym_split_planner.config import get_settings
from gym_split_planner.db.engine import make_engine
from gym_split_planner.db.migrate import current_revision, upgrade_to_head


def _migrate() -> None:
    engine = make_engine(get_settings().database_url)
    upgrade_to_head(engine)
    print(f"Database alla revisione {current_revision(engine)}")
    engine.dispose()


def _openapi() -> None:
    schema = create_app().openapi()
    json.dump(schema, sys.stdout, indent=2, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="gym_split_planner")
    parser.add_argument("command", choices=["migrate", "openapi"])
    args = parser.parse_args(argv)
    if args.command == "migrate":
        _migrate()
    else:
        _openapi()


if __name__ == "__main__":
    main()
