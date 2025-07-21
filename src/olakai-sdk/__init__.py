"""
Olakai SDK for monitoring and tracking AI/ML model interactions.
"""

from .client import (
    init_client,
    send_to_api, 
    get_config,
    get_queue_size,
    clear_queue,
    flush_queue
)
from .monitor import add_middleware, remove_middleware
from .types import SDKConfig, MonitorOptions, Middleware, MonitorPayload
from .logger import get_default_logger, safe_log
from .utils import MonitorUtils, olakai_monitor

__version__ = "0.1.0"

__all__ = [
    "init_client",
    "olakai_monitor", 
    "send_to_api",
    "get_config",
    "get_queue_size", 
    "clear_queue",
    "flush_queue",
    "add_middleware",
    "remove_middleware",
    "SDKConfig",
    "MonitorOptions", 
    "Middleware",
    "MonitorPayload",
    "get_default_logger",
    "safe_log",
    "MonitorUtils"
]
