from app.api.routers.analytics import router as analytics_router
from app.api.routers.chat import router as chat_router
from app.api.routers.insights import router as insights_router

__all__ = [
    "analytics_router",
    "chat_router",
    "insights_router",
]
