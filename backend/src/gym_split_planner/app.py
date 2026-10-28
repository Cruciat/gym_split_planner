"""Composizione dell'applicazione: unico punto che collega configurazione, database e API."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute

from gym_split_planner import __version__
from gym_split_planner.api.errors import install_error_handlers
from gym_split_planner.api.router import api_router
from gym_split_planner.api.spa import install_spa
from gym_split_planner.config import Settings, get_settings
from gym_split_planner.db.backup import run_daily_backup, sqlite_path
from gym_split_planner.db.engine import make_engine

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Crea l'applicazione FastAPI.

    Le migrazioni non partono da qui: le applica il comando ``migrate`` prima di
    avviare il server (ADR 0009), così un errore di migrazione blocca l'avvio
    invece di lasciare un'app a metà.
    """
    settings = settings or get_settings()

    @contextlib.asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        task = _start_backups(settings)
        yield
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    app = FastAPI(
        title="Gym Split Planner",
        version=__version__,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url=None,
        generate_unique_id_function=_operation_id,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.engine = make_engine(settings.database_url)

    install_error_handlers(app)
    app.include_router(api_router, prefix="/api")

    if settings.static_dir is not None and (settings.static_dir / "index.html").is_file():
        install_spa(app, settings.static_dir)

    return app


def _operation_id(route: APIRoute) -> str:
    """Usa il nome della funzione come operationId: tipi del client leggibili (``get_health``)."""
    return route.name


def _start_backups(settings: Settings) -> "asyncio.Task[None] | None":
    """Avvia il controllo periodico del backup giornaliero, se applicabile."""
    database = sqlite_path(settings.database_url)
    if not settings.backup_enabled or database is None:
        return None
    backup_dir = settings.backup_dir or database.parent / "backups"
    return asyncio.create_task(
        _backup_loop(database, backup_dir, settings.backup_keep, settings.backup_check_seconds)
    )


async def _backup_loop(database: Path, backup_dir: Path, keep: int, interval: int) -> None:
    """Ogni ``interval`` secondi: se manca il backup di oggi lo crea (anche dopo un riavvio)."""
    while True:
        try:
            await asyncio.to_thread(run_daily_backup, database, backup_dir, date.today(), keep)
        except Exception:
            # Un backup fallito non deve fermare l'app: si riprova al giro successivo.
            logger.exception("Backup del database non riuscito")
        await asyncio.sleep(interval)
