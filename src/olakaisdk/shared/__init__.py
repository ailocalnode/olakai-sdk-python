"""
Simplified shared module for the Olakai SDK.

This module provides common utilities, exceptions, and types used across the SDK.
"""

from .exceptions import (
    OlakaiSDKError,
    OlakaiBlockedError,
    APIKeyMissingError,
    URLConfigurationError,
    APITimeoutError,
    APIResponseError,
    RetryExhaustedError,
    InitializationError,
    ControlServiceError,
)
from .types import (
    OlakaiConfig,
    OlakaiEventParams,
    MonitorOptions,
    MonitorPayload,
    ControlPayload,
    APIResponse,
    ControlResponse,
    ControlDetails,
    MonitoringResponse,
)

__all__ = [
    # Exceptions
    "OlakaiSDKError",
    "OlakaiBlockedError",
    "APIKeyMissingError",
    "URLConfigurationError",
    "APITimeoutError",
    "APIResponseError",
    "RetryExhaustedError",
    "InitializationError",
    "ControlServiceError",
    # Types
    "OlakaiConfig",
    "OlakaiEventParams",
    "MonitorOptions",
    "MonitorPayload",
    "ControlPayload",
    "APIResponse",
    "ControlResponse",
    "ControlDetails",
    "MonitoringResponse",
]
