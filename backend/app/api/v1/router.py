from fastapi import APIRouter
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.insights import router as insights_router
from backend.app.api.v1.videos import router as videos_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(videos_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(insights_router)

