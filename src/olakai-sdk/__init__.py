"""
Olakai SDK for monitoring and tracking AI/ML model interactions.
"""

from .client import (
    init_client,
    get_config,
    get_queue_size,
    clear_queue,
    flush_queue
)
from .monitor import add_middleware, remove_middleware
from .client.types import SDKConfig
from .monitor.types import MonitorOptions, Middleware, MonitorUtils
from .shared.logger import get_default_logger, safe_log
from .helpers import olakai_monitor

__version__ = "0.1.0"

__all__ = [
    "init_client",
    "olakai_monitor", 
    "get_config",
    "get_queue_size", 
    "clear_queue",
    "flush_queue",
    "add_middleware",
    "remove_middleware",
    "SDKConfig",
    "MonitorOptions", 
    "Middleware",
    "get_default_logger",
    "safe_log",
    "MonitorUtils"
]
