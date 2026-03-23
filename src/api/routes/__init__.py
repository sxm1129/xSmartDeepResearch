"""Routes 模块"""

from .research import router as research_router
from .settings import router as settings_router
from .health import router as health_router
from .advanced_research import router as advanced_research_router

__all__ = ["research_router", "settings_router", "health_router", "advanced_research_router"]
