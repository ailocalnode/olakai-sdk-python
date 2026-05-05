"""
Simplified client for the Olakai SDK.
"""

from typing import Optional

from ..shared import (
    InitializationError,
)


def init_olakai_client(api_key: str, domain: Optional[str] = None, **kwargs):
    """
    Initialize the Olakai SDK client (legacy function for backward compatibility).

    Args:
        api_key: Your Olakai API key
        domain: API domain (full URL or bare hostname). If omitted, the
            target host is resolved from the `OLAKAI_HOST` env var, falling
            back to "app.olakai.ai". Bare hostnames go through the same
            normalization as `olakai_config(host=...)` (loopback hosts
            default to http://, others to https://). Full URLs preserve
            any embedded path for backward compatibility.
        **kwargs: Additional configuration (ignored in simplified version)
    """
    from ..config import olakai_config

    if domain is None:
        olakai_config(api_key, debug=kwargs.get("debug", False))
        return

    # Bare hostname → use `host` so loopback http:// special-case applies.
    # Full URL → use `endpoint` so embedded paths are preserved (legacy).
    if "://" in domain:
        olakai_config(
            api_key,
            endpoint=domain,
            debug=kwargs.get("debug", False),
        )
    else:
        olakai_config(
            api_key,
            host=domain,
            debug=kwargs.get("debug", False),
        )


def get_olakai_client():
    """
    Get the global Olakai client instance (legacy function for backward compatibility).
    """
    from ..config import get_config

    config = get_config()
    if config is None:
        raise InitializationError(
            "Olakai client not initialized. Please call olakai_config() first."
        )
    return config
