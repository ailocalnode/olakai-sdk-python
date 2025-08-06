"""
Shared module for the Olakai SDK.

This module provides common utilities, exceptions, logging, and types used across the SDK.
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
    MiddlewareError,
    ControlServiceError,
    QueueNotInitializedError,
    SanitizationError,
)
from .logger import safe_log, set_logger_level
from .types import APIResponse, ControlResponse, ControlDetails
from .utils import (
    create_error_info,
    to_string_api,
    fire_and_forget,
    sleep,
    generate_random_id,
    get_executor,
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
    "MiddlewareError",
    "ControlServiceError",
    "QueueNotInitializedError",
    "SanitizationError",
    # Logger
    "safe_log",
    "set_logger_level",
    # Types
    "APIResponse",
    "ControlResponse",
    "ControlDetails",
    # Utils
    "create_error_info",
    "to_string_api",
    "fire_and_forget",
    "sleep",
    "generate_random_id",
    "get_executor",
]