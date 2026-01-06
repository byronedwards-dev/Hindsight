from fastapi import APIRouter
from app.api import scenarios, games, leaderboard, auth

api_router = APIRouter()

api_router.include_router(auth.router)  # No prefix, auth has its own
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
api_router.include_router(games.router, prefix="/games", tags=["games"])
api_router.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])


