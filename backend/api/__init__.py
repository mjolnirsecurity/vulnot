"""VULNOT API Routes"""
from .process import router as process_router
from .alarms import router as alarms_router
from .system import router as system_router
__all__ = ["process_router", "alarms_router", "system_router"]
