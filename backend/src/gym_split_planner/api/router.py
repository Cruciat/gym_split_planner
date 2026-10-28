"""Router principale dell'API, montato sotto ``/api``."""

from fastapi import APIRouter

from gym_split_planner.api.routes import health, pdf

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(pdf.router)
