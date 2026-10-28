"""Controllo ottimistico con revisione (API, § 4): ``ETag`` e ``If-Match`` delle schede."""

from fastapi import Response

from gym_split_planner.api.errors import ApiProblem

PRECONDITION_RESPONSES: dict[int | str, dict[str, str]] = {
    404: {"description": "Scheda inesistente (`not-found`)"},
    412: {"description": "Revisione non aggiornata (`revision-mismatch`, con `current_revision`)"},
    428: {"description": "Manca `If-Match` (`revision-required`)"},
}


def expected_revision(if_match: str | None) -> int:
    """Revisione indicata dal client in ``If-Match`` (``"17"``, ``W/"17"`` o ``17``).

    Senza intestazione: ``428 revision-required``. Un valore illeggibile vale come
    revisione sbagliata: il servizio risponderà ``412`` con quella attuale.
    """
    if if_match is None:
        raise ApiProblem(
            428,
            "revision-required",
            "Revisione mancante",
            "Le modifiche a una scheda richiedono l'intestazione If-Match con la revisione.",
        )
    value = if_match.strip().removeprefix("W/").strip('"')
    try:
        return int(value)
    except ValueError:
        return -1


def set_etag(response: Response, revision: int) -> None:
    """Ogni risposta con una scheda porta la sua revisione come ``ETag`` (C3)."""
    response.headers["ETag"] = f'"{revision}"'
