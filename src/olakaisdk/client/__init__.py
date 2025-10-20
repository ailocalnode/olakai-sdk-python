"""
Simplified client module for the Olakai SDK.

This module provides simplified client configuration and API communication.
"""

from .client import init_olakai_client, get_olakai_client
from .api import send_to_api_simple

__all__ = [
    "init_olakai_client",
    "get_olakai_client",
    "send_to_api_simple",
]
