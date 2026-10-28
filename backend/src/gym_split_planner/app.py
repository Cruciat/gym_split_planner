"""Composizione dell'applicazione: unico punto che collega configurazione, database e API."""

from fastapi import FastAPI
from fastapi.routing import APIRoute

from gym_split_planner import __version__
from gym_split_planner.api.errors import install_error_handlers
from gym_split_planner.api.router import api_router
from gym_split_planner.api.spa import install_spa
from gym_split_planner.config import Settings, get_settings
from gym_split_planner.db.engine import make_engine


def create_app(settings: Settings | None = None) -> FastAPI:
    """Crea l'applicazione FastAPI.

    Le migrazioni non partono da qui: le applica il comando ``migrate`` prima di
    avviare il server (ADR 0009), così un errore di migrazione blocca l'avvio
    invece di lasciare un'app a metà.
    """
    settings = settings or get_settings()

    app = FastAPI(
        title="Gym Split Planner",
        version=__version__,
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url=None,
        generate_unique_id_function=_operation_id,
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
