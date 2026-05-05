"""Global configuration for Olakai SDK."""

import os
import re
from typing import Optional
from urllib.parse import urlparse

from .shared.types import OlakaiConfig
from .shared.exceptions import APIKeyMissingError, URLConfigurationError


_global_config: Optional[OlakaiConfig] = None

DEFAULT_HOST = "app.olakai.ai"

# Loopback hostnames default to http:// because local Olakai dev servers
# (e.g. `pnpm dev` on `localhost:3000`) don't usually have TLS.
# Match `localhost`, `127.0.0.1`, or IPv6 `[::1]`, with an optional port.
_LOOPBACK_HOST_RE = re.compile(
    r"^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
    re.IGNORECASE,
)


def _normalize_host(raw: str) -> str:
    """Normalize a `host` value into a `scheme://host[:port]` origin.

    Accepts a bare hostname (`olakai.acme.com`) or a full URL
    (`https://olakai.acme.com/api/v1`). For full URLs, only the origin is
    kept — paths, queries, and any userinfo (`user:pass@`) are stripped to
    avoid leaking credentials into debug logs. Bare hostnames default to
    `https://` except loopback hosts (`localhost`, `127.0.0.1`, `[::1]`,
    with optional port) which default to `http://` for local-dev convenience.

    Raises:
        URLConfigurationError: if the input is not a valid http/https URL.
    """
    raw = raw.strip().rstrip("/")
    if "://" in raw:
        parsed = urlparse(raw)
        if not parsed.netloc:
            raise URLConfigurationError(f"Invalid URL: {raw}")
        if parsed.scheme not in ("http", "https"):
            raise URLConfigurationError(
                f"Unsupported URL scheme '{parsed.scheme}' (expected http or https): {raw}"
            )
        # Strip userinfo (everything before "@") to keep credentials out of
        # the resolved endpoint and out of debug logs. Preserves IPv6
        # brackets and explicit ports because we keep the rest of netloc
        # verbatim.
        netloc = parsed.netloc.rsplit("@", 1)[-1]
        return f"{parsed.scheme}://{netloc}"
    scheme = "http" if _LOOPBACK_HOST_RE.match(raw) else "https"
    return f"{scheme}://{raw}"


def _resolve_endpoint(endpoint: Optional[str], host: Optional[str]) -> str:
    """
    Resolve the API endpoint URL.

    Precedence: explicit `endpoint` (full URL, may include path) →
    explicit `host` (bare hostname or full URL — origin-only) →
    `OLAKAI_HOST` env var → default `https://app.olakai.ai`.

    Trailing slashes are stripped so callers can safely append `/api/...`.
    Empty-string `endpoint` is treated as "not provided" rather than as a
    valid relative-URL endpoint.

    Raises:
        URLConfigurationError: if `endpoint`, `host`, or `OLAKAI_HOST` is
            not a valid http/https URL.
    """
    if endpoint:
        # `endpoint` preserves any embedded path (legacy contract), but it
        # must still be an http(s) URL — bare hostnames or non-http schemes
        # would silently produce malformed requests downstream.
        if "://" in endpoint:
            scheme = urlparse(endpoint).scheme
            if scheme not in ("http", "https"):
                raise URLConfigurationError(
                    f"Unsupported URL scheme '{scheme}' (expected http or https): {endpoint}"
                )
        else:
            raise URLConfigurationError(
                f"`endpoint` must be a full URL with http(s) scheme: {endpoint}. "
                f"Pass a bare hostname via `host=` instead."
            )
        return endpoint.rstrip("/")
    raw = host or os.environ.get("OLAKAI_HOST") or DEFAULT_HOST
    return _normalize_host(raw)


def olakai_config(
    api_key: str,
    endpoint: Optional[str] = None,
    debug: bool = False,
    host: Optional[str] = None,
) -> None:
    """
    Initialize the Olakai SDK.

    This should be called once at application startup before any
    instrumentation or monitoring.

    Args:
        api_key: Your Olakai API key
        endpoint: Full API endpoint URL with http(s) scheme
            (e.g. "https://app.olakai.ai"). If omitted, derived from
            `host` / `OLAKAI_HOST` env var / default "app.olakai.ai".
            Use this only when you need a non-default URL path;
            otherwise prefer `host`.
        debug: Enable debug logging (default: False)
        host: Olakai hostname only (e.g. "olakai.acme.com"). For on-prem
            deployments. Falls back to the `OLAKAI_HOST` env var, then
            "app.olakai.ai". Ignored if `endpoint` is provided.

    Raises:
        APIKeyMissingError: If api_key is empty or None.
        URLConfigurationError: If `endpoint`, `host`, or `OLAKAI_HOST`
            is not a valid http/https URL.

    Example:
        >>> from olakaisdk import olakai_config
        >>> # SaaS default
        >>> olakai_config("your-api-key")
        >>> # On-prem via host arg
        >>> olakai_config("your-api-key", host="olakai.acme.com")
        >>> # On-prem via OLAKAI_HOST env var (no host arg needed)
        >>> olakai_config("your-api-key", debug=True)
    """
    global _global_config

    if not api_key:
        raise APIKeyMissingError("API key is required to initialize the Olakai SDK")

    resolved_endpoint = _resolve_endpoint(endpoint, host)

    _global_config = OlakaiConfig(
        api_key=api_key,
        endpoint=resolved_endpoint,
        debug=debug,
    )

    if debug:
        print(f"[Olakai SDK] SDK initialized with endpoint: {resolved_endpoint}")


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
