"""
Client for the Olakai SDK.
"""

'''from ..monitor import olakai_monitor


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
                    f"Invalid configuration parameter: {key}, continuing anyway...",
                )
        safe_log(
            "info", f"Initialized Olakai SDK client with config: {self.config}"
        )

        # Load persisted queue (import here to avoid circular dependency)
        if self.config.enableStorage:
            try:
                from ..queueManagerPackage import (
                    init_queue_manager,
                    QueueDependencies,
                )
                from ..client.api import send_with_retry

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

    def monitor(self, **kwargs):
        """Create a monitoring decorator bound to this client instance."""
        return olakai_monitor(self.config, **kwargs)
'''
