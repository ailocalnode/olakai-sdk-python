"""
Client module for the Olakai SDK.

This module provides API communication, client configuration, and type definitions.
"""

# from .client import OlakaiClient
from .api import send_to_api

__all__ = [
    # "OlakaiClient",
    "send_to_api",
]
