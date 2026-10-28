"""Router principale dell'API, montato sotto ``/api``."""

from fastapi import APIRouter

from gym_split_planner.api.routes import (
    catalog,
    exercises,
    families,
    health,
    muscles,
    pdf,
    plan_edit,
    plans,
    settings,
    sources,
    tags,
)

api_router = APIRouter()
for module in (
    health,
    catalog,
    exercises,
    sources,
    families,
    muscles,
    tags,
    plans,
    plan_edit,
    settings,
    pdf,
):
    api_router.include_router(module.router)
