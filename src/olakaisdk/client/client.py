"""
Simplified client for the Olakai SDK.
"""

from ..shared import (
    OlakaiConfig,
    InitializationError,
    APIKeyMissingError,
    URLConfigurationError,
)


def init_olakai_client(api_key: str, domain: str = "https://app.olakai.ai", **kwargs):
    """
    Initialize the Olakai SDK client (legacy function for backward compatibility).
    
    Args:
        api_key: Your Olakai API key
        domain: API domain
        **kwargs: Additional configuration (ignored in simplified version)
    """
    from ..core import olakai_config
    
    # Convert domain to endpoint format
    endpoint = domain if domain.startswith("http") else f"https://{domain}"
    
    # Initialize with simplified config
    olakai_config(api_key, endpoint, debug=kwargs.get("debug", False))


def get_olakai_client():
    """
    Get the global Olakai client instance (legacy function for backward compatibility).
    """
    from ..core import get_config
    
    config = get_config()
    if config is None:
        raise InitializationError(
            "Olakai client not initialized. Please call olakai_config() first."
        )
    return config
