"""
Common types used across the SDK.
"""
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class APIResponse:
    """Response from API calls."""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None 

@dataclass
class ControlResponse:
    """Response from control API calls."""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None 