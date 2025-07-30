"""
Olakai SDK for monitoring and tracking AI/ML model interactions.
"""

from .client.client import OlakaiClient

from .monitor.middleware import add_middleware, remove_middleware
from .monitor.decorator import olakai_monitor
from .client.types import SDKConfig
from .monitor.types import MonitorOptions, Middleware, MonitorUtils
from .shared.exceptions import OlakaiFunctionBlocked

__version__ = "0.1.0"

__all__ = [
    "OlakaiClient",
    "olakai_monitor", 
    "add_middleware",
    "remove_middleware",
    "SDKConfig",
    "MonitorOptions", 
    "Middleware",
    "MonitorUtils",
    "OlakaiFunctionBlocked",
]
