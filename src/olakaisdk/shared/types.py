"""
Common types used across the SDK.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class MonitoringResponse:
    """Response from monitoring API calls."""

    index: int
    success: bool
    promptRequestId: Optional[str] = None
    error: Optional[str] = None


@dataclass
class APIResponse:
    """Response from API calls."""

    success: bool
    totalRequests: int
    successCount: int
    failureCount: int
    results: List[MonitoringResponse]
    message: Optional[str] = None


@dataclass
class ControlDetails:
    detectedSensitivity: List[str]
    isAllowedPersona: bool


@dataclass
class ControlResponse:
    """Response from control API calls."""

    allowed: bool
    details: ControlDetails
    message: Optional[str] = None
