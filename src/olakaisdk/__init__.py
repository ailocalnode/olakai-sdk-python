"""
Olakai SDK for monitoring and tracking AI/ML model interactions.
"""

from .client import init_olakai_client

from .monitor import (
    add_middleware,
    remove_middleware,
    olakai_supervisor,
)  # For backward compatibility
from .shared import OlakaiBlockedError, MonitorOptions, MonitorUtils

__version__ = "0.3.4"

__all__ = [
    "init_olakai_client",
    "olakai_supervisor",
    "MonitorOptions",
    "MonitorUtils",
    "OlakaiBlockedError",
    "add_middleware",  # Deprecated but available
    "remove_middleware",  # Deprecated but available
]
