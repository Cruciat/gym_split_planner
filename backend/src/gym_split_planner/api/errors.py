"""Errori in formato Problem Details (RFC 9457), come da contratto delle API (§ 3)."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from gym_split_planner.services.errors import (
    InUseError,
    InvalidBandError,
    NotFoundError,
    RuleViolationError,
    ServiceError,
)

logger = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"

# Codici e titoli per gli stati HTTP generati dal framework.
_DEFAULT_PROBLEMS: dict[int, tuple[str, str]] = {
    404: ("not-found", "Risorsa non trovata"),
    405: ("method-not-allowed", "Metodo non consentito"),
}


class ApiProblem(Exception):
    """Errore da restituire al client in formato Problem Details.

    ``code`` è stabile e serve al client per decidere cosa fare; ``title`` e ``detail``
    sono in italiano e si possono mostrare all'utente. ``extra`` aggiunge campi
    specifici del codice (es. ``current_revision``).
    """

    def __init__(
        self,
        status: int,
        code: str,
        title: str,
        detail: str | None = None,
        **extra: Any,
    ) -> None:
        super().__init__(title)
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail
        self.extra = extra


def problem_response(
    status: int,
    code: str,
    title: str,
    detail: str | None = None,
    **extra: Any,
) -> JSONResponse:
    """Costruisce la risposta JSON di un problema."""
    body: dict[str, Any] = {"type": "about:blank", "title": title, "status": status, "code": code}
    if detail is not None:
        body["detail"] = detail
    body.update(extra)
    return JSONResponse(status_code=status, content=body, media_type=PROBLEM_JSON)


async def _handle_api_problem(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiProblem)
    return problem_response(exc.status, exc.code, exc.title, exc.detail, **exc.extra)


async def _handle_service_error(_request: Request, exc: Exception) -> JSONResponse:
    """Errori previsti dei casi d'uso → Problem Details con il ``code`` del contratto."""
    assert isinstance(exc, ServiceError)
    if isinstance(exc, NotFoundError):
        return problem_response(404, "not-found", exc.title, exc.detail)
    if isinstance(exc, InUseError):
        return problem_response(409, "in-use", exc.title, exc.detail, usage=dict(exc.usage))
    if isinstance(exc, InvalidBandError):
        return problem_response(
            409,
            "invalid-band",
            exc.title,
            exc.detail,
            plans=[{"id": plan.id, "name": plan.name} for plan in exc.plans],
        )
    if isinstance(exc, RuleViolationError):
        first = exc.errors[0]
        return problem_response(
            422,
            "rule-violation",
            exc.title,
            exc.detail,
            rule=first.rule,
            violations=[
                {"rule": e.rule, "field": e.field, "message": e.message} for e in exc.errors
            ],
        )
    logger.error("Errore di servizio senza traduzione: %s", type(exc).__name__)
    return problem_response(500, "internal-error", "Errore interno", exc.title)


async def _handle_http_exception(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    known = _DEFAULT_PROBLEMS.get(exc.status_code)
    if known is not None:
        # Il dettaglio del framework è in inglese ("Not Found"): per questi stati basta il titolo.
        return problem_response(exc.status_code, *known)
    detail = exc.detail if isinstance(exc.detail, str) else None
    return problem_response(exc.status_code, "http-error", "Errore nella richiesta", detail)


async def _handle_validation_error(_request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = [
        {
            "loc": list(error.get("loc", ())),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        for error in exc.errors()
    ]
    return problem_response(
        422,
        "validation-error",
        "Dati non validi",
        "Alcuni campi della richiesta non sono validi.",
        errors=errors,
    )


async def _handle_unexpected(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Errore imprevisto", exc_info=exc)
    return problem_response(
        500,
        "internal-error",
        "Errore interno",
        "Si è verificato un errore imprevisto. Il dettaglio è nei log del server.",
    )


def install_error_handlers(app: FastAPI) -> None:
    """Registra i gestori che trasformano ogni errore in Problem Details."""
    app.add_exception_handler(ApiProblem, _handle_api_problem)
    app.add_exception_handler(ServiceError, _handle_service_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected)
