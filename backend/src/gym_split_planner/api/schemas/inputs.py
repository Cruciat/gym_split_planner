"""Tipi comuni dei corpi delle richieste: testi ripuliti e indirizzi web sicuri."""

from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, StringConstraints


def _blank_to_none(value: object) -> object:
    """Un testo vuoto o di soli spazi in un campo facoltativo vale come assente."""
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _http_url(value: str | None) -> str | None:
    """Solo indirizzi web: il link si apre nel browser, ``javascript:`` non deve passare."""
    if value is not None and not value.lower().startswith(("http://", "https://")):
        raise ValueError("L'indirizzo deve iniziare con http:// o https://")
    return value


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
"""Nome obbligatorio (esercizi, fonti), senza spazi ai bordi."""

Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
"""Testo breve obbligatorio (es. il tipo di una fonte, il nome di una famiglia)."""

ShortLabel = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
"""Nome breve obbligatorio, per tabelle strette e PDF (es. il nome breve di un muscolo)."""

ShortText = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None,
    BeforeValidator(_blank_to_none),
]
"""Testo breve facoltativo: vuoto → ``null``."""

LongText = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)] | None,
    BeforeValidator(_blank_to_none),
]
"""Note e descrizioni facoltative: vuoto → ``null``."""

HttpUrl = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None,
    BeforeValidator(_blank_to_none),
    AfterValidator(_http_url),
]
"""Indirizzo web facoltativo, solo ``http`` o ``https``."""


def reject_null(value: object) -> object:
    """In una modifica parziale un campo obbligatorio si può omettere, non svuotare.

    Da usare con ``field_validator(..., mode="after")``: non scatta per i campi
    omessi, perché i valori predefiniti non vengono validati.
    """
    if value is None:
        raise ValueError("Il campo non può essere vuoto")
    return value
