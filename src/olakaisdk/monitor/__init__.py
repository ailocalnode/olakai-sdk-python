"""
Simplified monitor module for the Olakai SDK.

This module provides simplified function monitoring and decorator functionality.
"""

from .decorator import olakai_monitor, olakai_supervisor

__all__ = [
    "olakai_monitor",
    "olakai_supervisor",  # Legacy function for backward compatibility
]
