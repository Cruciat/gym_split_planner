"""Router principale dell'API, montato sotto ``/api``."""

from fastapi import APIRouter

from gym_split_planner.api.routes import (
    catalog,
    exercises,
    families,
    health,
    muscles,
    pdf,
    sources,
    tags,
)

api_router = APIRouter()
for module in (health, catalog, exercises, sources, families, muscles, tags, pdf):
    api_router.include_router(module.router)
