"""
Configuration management for the Olakai SDK client.
"""
import logging
from typing import Optional
from .types import SDKConfig
from ..shared.exceptions import InitializationError, ConfigNotInitializedError

# Global configuration
config = SDKConfig(
    apiKey="",
    monitoringUrl="",
    controlUrl="",
)


async def init_client(
    api_key: str, 
    domain: str = "https://app.olakai.ai", 
    logger: Optional[logging.Logger] = None,
    **kwargs
):
    """
    Initialize the Olakai SDK client.
    
    Args:
        api_key: Your Olakai API key
        domain: API domain (default: app.olakai.ai)
        sdk_config: Optional SDK configuration
        logger: Optional logger instance for logging SDK operations
    """
    global config
    if logger is None:
        config.logger = logging.getLogger('OlakaiSDK')
    else:
        config.logger = logger
    
    config.apiKey = api_key
    config.monitoringUrl = f"{domain}/api/monitoring/prompt" if domain else "https://staging.app.olakai.ai/api/monitoring/prompt"
    config.controlUrl = f"{domain}/api/control/prompt" if domain else "https://staging.app.olakai.ai/api/control/prompt"
    
    from ..shared.logger import safe_log
    for key, value in kwargs.items():
        try:
            setattr(config, key, value)
        except AttributeError:
            safe_log('warning', f"Invalid configuration parameter: {key}, continuing anyway...")
    safe_log('info', f"Initialized Olakai SDK client with config: {config}")
    
    # Load persisted queue (import here to avoid circular dependency)
    if config.enableStorage:
        try:
            from ..queueManagerPackage import init_queue_manager, QueueDependencies
            from ..client.api import send_with_retry
            await init_queue_manager(QueueDependencies(config, send_with_retry))
        except Exception as e:
            raise InitializationError(f"Failed to initialize queue manager: {str(e)}") from e
    if config.debug:
        config.logger.setLevel(logging.INFO)
    if config.verbose:
        config.logger.setLevel(logging.DEBUG)
    else:
        config.logger.setLevel(logging.WARNING)


def get_config() -> SDKConfig:
    """Get the current SDK configuration."""
    if config is None:
        raise ConfigNotInitializedError("[Olakai SDK] Config is not initialized")
    return config 