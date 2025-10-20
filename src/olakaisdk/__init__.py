"""
Simplified Olakai SDK for monitoring and tracking AI/ML model interactions.
"""

from .core import olakai_config, olakai, olakai_report, olakai_monitor, get_config
from .monitor import olakai_supervisor  # Legacy function for backward compatibility
from .shared import OlakaiBlockedError, MonitorOptions, OlakaiEventParams, OlakaiConfig

__version__ = "0.4.0"

__all__ = [
    # New simplified API
    "olakai_config",
    "olakai", 
    "olakai_report",
    "olakai_monitor",
    "get_config",
    # Types
    "MonitorOptions",
    "OlakaiEventParams", 
    "OlakaiConfig",
    "OlakaiBlockedError",
    # Legacy functions for backward compatibility
    "olakai_supervisor",
]
