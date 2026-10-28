"""Fonti della ricerca: creazione, modifica, eliminazione (API, § 6.3; per la form di US-03)."""

from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy import Engine, select

from gym_split_planner.db.models import Source
from gym_split_planner.db.session import make_session_factory
from gym_split_planner.domain.catalog_rules import next_numbered_code
from gym_split_planner.services.catalog import SourceData
from gym_split_planner.services.errors import NotFoundError

CODE_PREFIX = "src"
"""Le fonti nuove continuano la numerazione dell'Excel: ``src-49``, ``src-50``…"""

EDITABLE = frozenset({"title", "kind", "url", "reliability", "used_for"})


@dataclass(frozen=True)
class SourceInput:
    title: str
    kind: str
    url: str | None
    reliability: str | None
    used_for: str | None


def create_source(engine: Engine, data: SourceInput) -> SourceData:
    """Crea una fonte con il primo codice libero della serie ``src-NN``."""
    with make_session_factory(engine)() as session:
        code = next_numbered_code(CODE_PREFIX, set(session.scalars(select(Source.code))))
        source = Source(
            code=code,
            title=data.title,
            kind=data.kind,
            url=data.url,
            reliability=data.reliability,
            used_for=data.used_for,
        )
        session.add(source)
        session.commit()
        return _data(source)


def update_source(engine: Engine, source_id: int, changes: Mapping[str, str | None]) -> SourceData:
    """Modifica parziale: cambiano solo i campi presenti in ``changes``."""
    unknown = set(changes) - EDITABLE
    if unknown:
        raise ValueError(f"Campi non modificabili: {sorted(unknown)}")
    with make_session_factory(engine)() as session:
        source = _load(session.get(Source, source_id), source_id)
        for field, value in changes.items():
            setattr(source, field, value)
        session.commit()
        return _data(source)


def delete_source(engine: Engine, source_id: int) -> None:
    """Elimina la fonte e i suoi collegamenti agli esercizi (modello dati, § 6)."""
    with make_session_factory(engine)() as session:
        session.delete(_load(session.get(Source, source_id), source_id))
        session.commit()


def _load(source: Source | None, source_id: int) -> Source:
    if source is None:
        raise NotFoundError("Fonte non trovata", f"Non esiste la fonte {source_id}.")
    return source


def _data(source: Source) -> SourceData:
    return SourceData(
        id=source.id,
        code=source.code,
        title=source.title,
        kind=source.kind,
        url=source.url,
        reliability=source.reliability,
        used_for=source.used_for,
    )
