"""
Olakai SDK for monitoring and tracking AI/ML model interactions.
"""

from .client.client import OlakaiClient

from .monitor.types import MonitorOptions, MonitorUtils
from .monitor.middleware import add_middleware, remove_middleware  # For backward compatibility
from .shared.exceptions import OlakaiFunctionBlocked

__version__ = "0.1.0"

__all__ = [
    "OlakaiClient",
    "MonitorOptions", 
    "MonitorUtils",
    "OlakaiFunctionBlocked",
    "add_middleware",  # Deprecated but available
    "remove_middleware",  # Deprecated but available
]
