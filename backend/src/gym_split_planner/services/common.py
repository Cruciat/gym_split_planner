"""Aiuti comuni ai casi d'uso del catalogo: nomi liberi, codici, ordine, riferimenti."""

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from gym_split_planner.domain.catalog_rules import is_valid_code, slugify, unique_code
from gym_split_planner.services.errors import RuleError

CODE_MAX_LENGTH = 60


def name_taken(
    session: Session,
    name_column: InstrumentedAttribute[str],
    id_column: InstrumentedAttribute[int],
    name: str,
    exclude_id: int | None = None,
) -> bool:
    """Vero se un'altra riga ha già questo nome, senza distinguere maiuscole."""
    condition: ColumnElement[bool] = func.lower(name_column) == name.lower()
    query = select(id_column).where(condition)
    if exclude_id is not None:
        query = query.where(id_column != exclude_id)
    return session.scalars(query).first() is not None


def new_code(
    session: Session,
    code_column: InstrumentedAttribute[str],
    name: str,
    requested: str | None,
) -> tuple[str, list[RuleError]]:
    """Codice per una riga nuova: quello richiesto se valido e libero, altrimenti dal nome."""
    taken = set(session.scalars(select(code_column)))
    if requested is None:
        base = slugify(name, max_length=CODE_MAX_LENGTH)
        return unique_code(base, taken, max_length=CODE_MAX_LENGTH), []
    if not is_valid_code(requested) or len(requested) > CODE_MAX_LENGTH:
        message = "Il codice può contenere solo minuscole, cifre e trattini tra le parole."
        return requested, [RuleError("invalid-code", "code", message)]
    if requested in taken:
        return requested, [RuleError("code-taken", "code", f"Il codice «{requested}» è già usato.")]
    return requested, []


def next_sort_order(session: Session, column: InstrumentedAttribute[int]) -> int:
    """Posizione dopo l'ultima: le righe nuove vanno in fondo all'elenco."""
    return int(session.scalar(select(func.max(column))) or 0) + 1


def unknown(field: str, message: str) -> RuleError:
    return RuleError("unknown-reference", field, message)
