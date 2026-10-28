"""Errori dei casi d'uso, tradotti in Problem Details dallo strato api (API, § 3).

I servizi non conoscono HTTP: dicono cosa è andato storto, l'api sceglie stato e
formato. Titoli e dettagli sono in italiano e arrivano all'utente così come sono.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


class ServiceError(Exception):
    """Base degli errori previsti dei casi d'uso."""

    def __init__(self, title: str, detail: str | None = None) -> None:
        super().__init__(title)
        self.title = title
        self.detail = detail


class NotFoundError(ServiceError):
    """La risorsa non esiste (``404 not-found``)."""


@dataclass(frozen=True)
class RuleError:
    """Una regola violata: ``rule`` stabile, ``field`` per mostrarla accanto al campo."""

    rule: str
    field: str | None
    message: str


class RuleViolationError(ServiceError):
    """Dati ben formati che violano regole del dominio (``422 rule-violation``)."""

    def __init__(self, errors: tuple[RuleError, ...]) -> None:
        if not errors:
            raise ValueError("Serve almeno una regola violata")
        super().__init__("Dati non accettati", " ".join(e.message for e in errors))
        self.errors = errors


class InUseError(ServiceError):
    """Eliminazione rifiutata perché la risorsa è usata (``409 in-use``)."""

    def __init__(self, title: str, detail: str, usage: Mapping[str, Any]) -> None:
        super().__init__(title, detail)
        self.usage = usage


@dataclass(frozen=True)
class PlanRef:
    """Scheda citata in un errore: ``id`` per il link, nome per il messaggio."""

    id: int
    name: str


class InvalidBandError(ServiceError):
    """Una modifica al catalogo lascerebbe una scheda con una fascia non valida (``409``)."""

    def __init__(self, plans: tuple[PlanRef, ...]) -> None:
        names = ", ".join(f"«{plan.name}»" for plan in plans)
        super().__init__(
            "Fascia non valida in una scheda",
            f"Con questa fascia la personalizzazione delle schede {names} non sarebbe più "
            "valida: correggila prima nelle preferenze della scheda.",
        )
        self.plans = plans


class RevisionMismatchError(ServiceError):
    """La scheda è cambiata dopo la revisione su cui il client lavorava (``412``, API § 4)."""

    def __init__(self, current_revision: int) -> None:
        super().__init__(
            "Revisione non aggiornata",
            "La scheda è stata modificata da un altro dispositivo.",
        )
        self.current_revision = current_revision
