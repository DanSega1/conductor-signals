from app.api.routers.analytics import router as analytics_router
from app.api.routers.auth import router as auth_router
from app.api.routers.chat import router as chat_router
from app.api.routers.insights import router as insights_router
from app.api.routers.settings import router as settings_router

__all__ = [
    "analytics_router",
    "auth_router",
    "chat_router",
    "insights_router",
    "settings_router",
]
