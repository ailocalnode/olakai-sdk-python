"""
Exceptions for the Olakai SDK.
"""

# Base exception for all Olakai SDK errors
class OlakaiSDKError(Exception):
    """Base exception for all Olakai SDK errors."""
    pass

# Function blocking exceptions
class OlakaiFunctionBlocked(OlakaiSDKError):
    """Exception raised when a function is blocked by Olakai monitoring."""
    def __init__(self, message: str, details: dict):
        super().__init__(message)
        self.details = details

# API and Configuration exceptions
class APIKeyMissingError(OlakaiSDKError):
    """Exception raised when API key is not configured."""
    pass

class URLConfigurationError(OlakaiSDKError):
    """Exception raised when required URLs are not configured."""
    pass

class APITimeoutError(OlakaiSDKError):
    """Exception raised when API requests timeout."""
    pass

class APIResponseError(OlakaiSDKError):
    """Exception raised when API returns an error response."""
    pass

class RetryExhaustedError(OlakaiSDKError):
    """Exception raised when all retry attempts have been exhausted."""
    pass

class InitializationError(OlakaiSDKError):
    """Exception raised when SDK initialization fails."""
    pass

# Monitoring and Processing exceptions
class MiddlewareError(OlakaiSDKError):
    """Exception raised when middleware processing fails."""
    pass

class MonitoringError(OlakaiSDKError):
    """Exception raised when monitoring capture fails."""
    pass

class SanitizationError(OlakaiSDKError):
    """Exception raised when data sanitization fails."""
    pass

class ControlServiceError(OlakaiSDKError):
    """Exception raised when control service communication fails."""
    pass

# Queue Management exceptions
class QueueNotInitializedError(OlakaiSDKError):
    """Exception raised when queue manager is not initialized."""
    pass

class ConfigNotInitializedError(OlakaiSDKError):
    """Exception raised when configuration is not initialized."""
    pass

