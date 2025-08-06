"""
Client for the Olakai SDK.
"""

from ..shared import SDKConfig, InitializationError, safe_log, set_logger_level, QueueDependencies, APIKeyMissingError, URLConfigurationError


class OlakaiClient:
    def __init__(
        self, api_key: str, domain: str = "https://app.olakai.ai", **kwargs
    ):
        """
        Initialize the Olakai SDK client.

        Args:
            api_key: Your Olakai API key
            domain: API domain (default: app.olakai.ai)
            logger: Optional logger instance for logging SDK operations
            **kwargs: Optional SDK configuration
        """
        if not api_key:
            raise APIKeyMissingError("API key is required to initialize the Olakai SDK client.")
        if not domain:
            raise URLConfigurationError("Domain is required to initialize the Olakai SDK client.")
        
        self.config = SDKConfig(
            apiKey=api_key,
            monitoringUrl=f"{domain}/api/monitoring/prompt"
            if domain
            else "https://staging.app.olakai.ai/api/monitoring/prompt",
            controlUrl=f"{domain}/api/control/prompt"
            if domain
            else "https://staging.app.olakai.ai/api/control/prompt",
            **kwargs,
        )

        for key, value in kwargs.items():
            try:
                setattr(self.config, key, value)
            except AttributeError:
                safe_log(
                    "warning",
                    f"Invalid configuration parameter: {key}. Proceeding with default value.",
                )
        safe_log(
            "info", f"Initialized Olakai SDK client with config: {self.config}"
        )

        # Load persisted queue (import here to avoid circular dependency)
        if self.config.enableStorage:
            try:
                from ..queueManagerPackage import (
                    init_queue_manager,
                )
                from .api import send_with_retry

                init_queue_manager(
                    QueueDependencies(self.config, send_with_retry)
                )
            except Exception as e:
                raise InitializationError(
                    f"Failed to initialize queue manager: {str(e)}"
                ) from e
        if self.config.debug:
            set_logger_level("info")
        if self.config.verbose:
            set_logger_level("debug")
        else:
            set_logger_level("warning")

    def get_config(self) -> SDKConfig:
        """Get the current SDK configuration."""
        return self.config


_global_client = None

def init_olakai_client(api_key: str, domain: str, **kwargs):
    """
    Initialize the Olakai SDK client.

    Args:
        api_key: Your Olakai API key
        domain: API domain
        **kwargs: Optional SDK configuration. See SDKConfig for more details.
    """
    global _global_client
    if _global_client is None:
        _global_client = OlakaiClient(api_key, domain, **kwargs)
    return _global_client

def get_olakai_client():
    """
    Get the global Olakai client instance.
    """
    if _global_client is None:
        raise InitializationError("Olakai client not initialized. Please call init_olakai_client first.")
    return _global_client