"""Sessioni SQLAlchemy."""

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Fabbrica di sessioni legata al motore. ``expire_on_commit=False`` lascia
    leggibili gli oggetti dopo il commit, per costruire le risposte."""
    return sessionmaker(bind=engine, expire_on_commit=False)
