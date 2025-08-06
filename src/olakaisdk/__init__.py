"""
Olakai SDK for monitoring and tracking AI/ML model interactions.
"""

from .client import OlakaiClient

from .monitor import MonitorOptions, MonitorUtils
from .monitor import (
    add_middleware,
    remove_middleware,
)  # For backward compatibility
from .shared import OlakaiBlockedError

__version__ = "0.3.4"

__all__ = [
    "OlakaiClient",
    "MonitorOptions",
    "MonitorUtils",
    "OlakaiBlockedError",
    "add_middleware",  # Deprecated but available
    "remove_middleware",  # Deprecated but available
]
