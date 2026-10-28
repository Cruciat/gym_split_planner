"""Applicazione delle migrazioni Alembic, usata all'avvio del container (ADR 0009)."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def alembic_config() -> Config:
    """Configurazione di Alembic che punta alle migrazioni incluse nel pacchetto."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    return config


def upgrade_to_head(engine: Engine) -> None:
    """Porta il database all'ultima revisione."""
    config = alembic_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def current_revision(engine: Engine) -> str | None:
    """Revisione applicata al database, ``None`` se non è mai stato migrato."""
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def head_revision() -> str | None:
    """Ultima revisione disponibile nel codice."""
    return ScriptDirectory.from_config(alembic_config()).get_current_head()
