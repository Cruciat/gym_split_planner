"""``GET /api/health`` (API, § 6.1)."""

from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from sqlalchemy import Engine

from gym_split_planner.services.health import check_health

router = APIRouter(tags=["sistema"])


class HealthOut(BaseModel):
    """Stato dell'applicazione."""

    status: Literal["ok", "error"]
    version: str
    database: Literal["ok", "error"]


@router.get(
    "/health",
    response_model=HealthOut,
    summary="Stato dell'applicazione",
    responses={503: {"model": HealthOut, "description": "Database non raggiungibile"}},
)
def get_health(request: Request, response: Response) -> HealthOut:
    """Usato dal controllo di salute del container: risponde 503 se il database non risponde."""
    engine: Engine = request.app.state.engine
    report = check_health(engine)
    if report.status != "ok":
        response.status_code = 503
    return HealthOut(status=report.status, version=report.version, database=report.database)
