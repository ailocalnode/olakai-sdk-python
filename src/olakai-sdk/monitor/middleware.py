"""
Middleware management for the Olakai SDK monitor.
"""
import logging
from typing import List, Optional
from .types import Middleware
from ..shared.logger import get_default_logger, safe_log

# Global middleware registry
middlewares: List[Middleware] = []


async def add_middleware(middleware: Middleware, logger: Optional[logging.Logger] = None) -> None:
    """Add middleware to the global middleware registry."""
    if logger is None:
        logger = await get_default_logger()
    middlewares.append(middleware)
    await safe_log(logger, 'info', f"Added middleware: {middleware.name}")


async def remove_middleware(name: str, logger: Optional[logging.Logger] = None) -> None:
    """Remove middleware from the global middleware registry."""
    if logger is None:
        logger = await get_default_logger()
    global middlewares
    middlewares = [m for m in middlewares if m.name != name]
    await safe_log(logger, 'info', f"Removed middleware: {name}")


def get_middlewares() -> List[Middleware]:
    """Get all registered middlewares."""
    return middlewares 