"""Base dichiarativa dei modelli SQLAlchemy."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Nomi espliciti per vincoli e indici: Alembic in modalità batch (necessaria su SQLite,
# ADR 0003) deve poterli riconoscere per ricreare le tabelle.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base di tutti i modelli. Le tabelle arrivano con M1 (modello dati)."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
