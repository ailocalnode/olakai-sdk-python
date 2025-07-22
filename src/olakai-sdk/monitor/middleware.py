"""
Middleware management for the Olakai SDK monitor.
"""
from typing import List
from .types import Middleware
from ..shared.logger import safe_log

# Global middleware registry
middlewares: List[Middleware] = []


async def add_middleware(middleware: Middleware) -> None:
    """Add middleware to the global middleware registry."""
    middlewares.append(middleware)
    safe_log('info', f"Added middleware: {middleware.name}")


async def remove_middleware(name: str) -> None:
    """Remove middleware from the global middleware registry."""
    global middlewares
    middlewares = [m for m in middlewares if m.name != name]
    safe_log('info', f"Removed middleware: {name}")


def get_middlewares() -> List[Middleware]:
    """Get all registered middlewares."""
    return middlewares 