"""Router principale dell'API, montato sotto ``/api``."""

from fastapi import APIRouter

from gym_split_planner.api.routes import catalog, exercises, health, pdf, sources

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(catalog.router)
api_router.include_router(exercises.router)
api_router.include_router(sources.router)
api_router.include_router(pdf.router)
