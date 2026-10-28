"""Tipi di colonna condivisi dai modelli (modello dati, § 1)."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Dialect, Enum, String
from sqlalchemy.types import TypeDecorator


class UtcDateTime(TypeDecorator[datetime]):
    """Data e ora in UTC, salvate come testo ISO 8601 (``2026-10-28T09:15:00Z``).

    Leggibili nel file SQLite e nell'esportazione; in lettura tornano ``datetime``
    con fuso UTC. Un valore senza fuso viene rifiutato: è quasi sempre un errore.
    """

    impl = String(20)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Data e ora senza fuso orario: usare datetime con tzinfo=UTC")
        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def process_result_value(self, value: str | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def utc_now() -> datetime:
    """Istante attuale in UTC, al secondo (la precisione salvata)."""
    return datetime.now(UTC).replace(microsecond=0)


def text_enum[E: StrEnum](enum: type[E], name: str) -> Enum:
    """Colonna testuale con ``CHECK`` sui valori ammessi (modello dati, § 1, punto 6).

    ``name`` diventa il nome del vincolo (``ck_<tabella>_<name>``).
    """
    return Enum(
        enum,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        length=max(len(member.value) for member in enum),
        values_callable=lambda members: [member.value for member in members],
    )


def flag(name: str) -> Boolean:
    """Booleano salvato come intero 0/1 con ``CHECK``."""
    return Boolean(create_constraint=True, name=name)
