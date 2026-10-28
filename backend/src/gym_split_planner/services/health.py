"""Controllo di salute dell'applicazione (API, § 6.1)."""

import logging
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from gym_split_planner import __version__

logger = logging.getLogger(__name__)

Status = Literal["ok", "error"]


@dataclass(frozen=True)
class HealthReport:
    """Esito del controllo di salute."""

    status: Status
    version: str
    database: Status


def check_health(engine: Engine) -> HealthReport:
    """Verifica che il database risponda. L'app è sana se e solo se il database lo è."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Controllo di salute: database non raggiungibile")
        return HealthReport(status="error", version=__version__, database="error")
    return HealthReport(status="ok", version=__version__, database="ok")
