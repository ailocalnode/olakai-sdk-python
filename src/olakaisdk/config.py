"""Global configuration for Olakai SDK."""

from typing import Optional
from .shared.types import OlakaiConfig
from .shared.exceptions import APIKeyMissingError


_global_config: Optional[OlakaiConfig] = None


def olakai_config(
    api_key: str,
    endpoint: str = "https://app.olakai.ai",
    debug: bool = False
) -> None:
    """
    Initialize the Olakai SDK.

    This should be called once at application startup before any
    instrumentation or monitoring.

    Args:
        api_key: Your Olakai API key
        endpoint: API endpoint URL (default: https://app.olakai.ai)
        debug: Enable debug logging (default: False)

    Raises:
        APIKeyMissingError: If api_key is empty or None

    Example:
        >>> from olakaisdk import olakai_config
        >>> olakai_config("your-api-key", debug=True)
    """
    global _global_config

    if not api_key:
        raise APIKeyMissingError("API key is required to initialize the Olakai SDK")

    _global_config = OlakaiConfig(
        api_key=api_key,
        endpoint=endpoint,
        debug=debug
    )

    if debug:
        print(f"[Olakai] SDK initialized with endpoint: {endpoint}")


def get_config() -> Optional[OlakaiConfig]:
    """
    Get the current SDK configuration.

    Returns:
        Current OlakaiConfig instance, or None if not initialized
    """
    return _global_config


def require_config() -> OlakaiConfig:
    """
    Get the configuration, raising an error if not initialized.

    Returns:
        Current OlakaiConfig instance

    Raises:
        RuntimeError: If SDK has not been initialized with olakai_config()
    """
    if _global_config is None:
        raise RuntimeError(
            "Olakai SDK not initialized. Call olakai_config() first."
        )
    return _global_config


def is_initialized() -> bool:
    """
    Check if the SDK has been initialized.

    Returns:
        True if olakai_config() has been called, False otherwise
    """
    return _global_config is not None
