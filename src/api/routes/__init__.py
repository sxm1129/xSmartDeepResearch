"""Routes 模块"""

from .research import router as research_router
from .settings import router as settings_router

__all__ = ["research_router", "settings_router"]
