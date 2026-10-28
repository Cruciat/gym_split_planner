"""Router principale dell'API, montato sotto ``/api``."""

from fastapi import APIRouter

from gym_split_planner.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router)
