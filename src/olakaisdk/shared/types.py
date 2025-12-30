"""
Simplified types for the Olakai SDK.
"""

from dataclasses import dataclass
from typing import Optional, List, Union, Dict

JSONType = Union[
    None, bool, int, float, str, Dict[str, "JSONType"], List["JSONType"]
]


@dataclass
class OlakaiConfig:
    """Simplified configuration for the SDK."""

    api_key: str
    endpoint: str = "https://app.olakai.ai"
    debug: bool = False


@dataclass
class OlakaiEventParams:
    """Parameters for event tracking."""

    prompt: str
    response: str
    userEmail: Optional[str] = "anonymous@olakai.ai"
    userId: Optional[str] = None  # SDK client's user ID for tracking
    chatId: Optional[str] = None
    task: Optional[str] = None
    subTask: Optional[str] = None
    customDimensions: Optional[Dict[str, str]] = None
    customMetrics: Optional[Dict[str, float]] = None
    shouldScore: bool = True
    tokens: Optional[int] = 0
    requestTime: Optional[int] = 0


@dataclass
class MonitorOptions:
    """Options for monitoring functions."""

    userEmail: Optional[str] = "anonymous@olakai.ai"
    userId: Optional[str] = None  # SDK client's user ID for tracking
    chatId: Optional[str] = None
    task: Optional[str] = None
    subTask: Optional[str] = None
    customDimensions: Optional[Dict[str, str]] = None
    customMetrics: Optional[Dict[str, float]] = None
    shouldScore: bool = True


@dataclass
class MonitorPayload:
    """Payload for monitoring data sent to API."""

    userEmail: str
    userId: Optional[str] = None  # SDK client's user ID for tracking
    chatId: str = ""
    prompt: JSONType = None
    response: JSONType = None
    blocked: Optional[bool] = False
    tokens: Optional[int] = 0
    requestTime: Optional[int] = 0
    task: Optional[str] = None
    subTask: Optional[str] = None
    errorMessage: Optional[str] = None
    sensitivity: Optional[List[str]] = None
    customDimensions: Optional[Dict[str, str]] = None
    customMetrics: Optional[Dict[str, float]] = None
    shouldScore: Optional[bool] = True


@dataclass
class ControlPayload:
    """Payload for control data sent to API."""

    prompt: JSONType
    email: Optional[str] = "anonymous@olakai.ai"
    chatId: Optional[str] = "123"
    task: Optional[str] = None
    subTask: Optional[str] = None
    tokens: Optional[int] = 0
    overrideControlCriteria: Optional[List[str]] = None


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
    results: Optional[List[MonitoringResponse]] = None
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
