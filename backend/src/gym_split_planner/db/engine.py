"""Creazione del motore SQLAlchemy con le impostazioni di SQLite richieste da ADR 0003."""

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url


def make_engine(url: str) -> Engine:
    """Crea il motore del database.

    Per SQLite: crea la cartella del file se manca e imposta a ogni connessione
    ``foreign_keys = ON`` (SQLite le ignora altrimenti) e ``journal_mode = WAL``
    (letture e scritture senza bloccarsi a vicenda, backup coerenti a caldo).
    """
    parsed = make_url(url)
    connect_args: dict[str, Any] = {}
    if parsed.get_backend_name() == "sqlite":
        # Uvicorn può servire richieste da thread diversi da quello che ha aperto la connessione.
        connect_args["check_same_thread"] = False
        database = parsed.database
        if database and database != ":memory:":
            Path(database).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url, connect_args=connect_args)

    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _set_sqlite_pragmas)

    return engine


def _set_sqlite_pragmas(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
    finally:
        cursor.close()
