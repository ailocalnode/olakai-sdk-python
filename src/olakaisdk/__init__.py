"""
Olakai SDK - Auto-instrumentation for LLM monitoring and tracking.

v0.5.0 introduces automatic instrumentation for OpenAI and other LLM providers.
"""

# New API (v0.5.0)
from .config import olakai_config, get_config, is_initialized
from .context import olakai_context, get_current_context
from .instrumentation import instrument_openai, uninstrument_openai, is_instrumented

# Legacy API (will be deprecated in future versions)
from .core import olakai, olakai_report, olakai_monitor
from .monitor import olakai_supervisor

# Types
from .shared import OlakaiBlockedError, MonitorOptions, OlakaiEventParams, OlakaiConfig

__version__ = "0.5.0"

__all__ = [
    # Primary API (v0.5.0)
    "olakai_config",           # Initialize SDK
    "instrument_openai",       # Auto-instrument OpenAI
    "uninstrument_openai",     # Remove instrumentation
    "olakai_context",         # Context manager for metadata
    "get_config",              # Get current config
    "is_initialized",          # Check if initialized
    "is_instrumented",         # Check if OpenAI is instrumented
    "get_current_context",     # Get current context data
    # Legacy API (for backward compatibility)
    "olakai",
    "olakai_report",
    "olakai_monitor",
    "olakai_supervisor",
    # Types
    "MonitorOptions",
    "OlakaiEventParams",
    "OlakaiConfig",
    "OlakaiBlockedError",
]
