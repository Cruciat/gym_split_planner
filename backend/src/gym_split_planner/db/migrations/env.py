"""Ambiente di Alembic.

Due modi d'uso:
- dall'app (``upgrade_to_head``): la connessione arriva in ``config.attributes["connection"]``;
- da riga di comando (``uv run alembic …`` nella cartella ``backend``): l'URL arriva da
  ``GSP_DATABASE_URL`` o, in mancanza, dal valore predefinito delle impostazioni.
"""

from alembic import context
from sqlalchemy import Connection

from gym_split_planner.config import get_settings
from gym_split_planner.db.base import Base
from gym_split_planner.db.engine import make_engine

target_metadata = Base.metadata


def _run(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # SQLite non sa modificare le colonne: Alembic ricrea la tabella (ADR 0003).
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = context.config.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return
    engine = make_engine(get_settings().database_url)
    with engine.begin() as new_connection:
        _run(new_connection)
    engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("La modalità offline di Alembic non è usata in questo progetto.")
run_migrations_online()
