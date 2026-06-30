from __future__ import annotations

from app.api.routers.analytics import router as analytics_router
from app.api.routers.insights import router as insights_router

__all__ = [
    "analytics_router",
    "insights_router",
]
