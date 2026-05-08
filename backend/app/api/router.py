from fastapi import APIRouter

from app.api.routes import chat, curriculum, health, mentors, news, onboarding, reports
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(health.router)

v1_router = APIRouter(prefix=settings.api_v1_prefix)
v1_router.include_router(mentors.router, prefix="/mentors", tags=["mentors"])
v1_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
v1_router.include_router(news.router, prefix="/news", tags=["news"])
v1_router.include_router(chat.router, prefix="/chat", tags=["chat"])
v1_router.include_router(reports.router, prefix="/reports", tags=["reports"])
v1_router.include_router(curriculum.router, prefix="/curriculum", tags=["curriculum"])

api_router.include_router(v1_router)

