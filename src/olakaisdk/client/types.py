"""
Types specific to client functionality (API communication, batching, configuration).
"""
from dataclasses import dataclass
from typing import Optional, List, Any
import logging

@dataclass
class MonitorPayload:
    """Payload for monitoring data sent to API."""
    email: str
    chatId: str
    prompt: str
    response: str
    shouldScore: bool
    tokens: Optional[int]
    requestTime: Optional[int]
    errorMessage: Optional[str]
    task: Optional[str]
    subTask: Optional[str]

@dataclass
class ControlPayload:
    """Payload for control data sent to API."""
    email: Optional[str] = "anonymous@olakai.ai"
    prompt: str
    askedOverrides: Optional[List[str]] = None

@dataclass
class BatchRequest:
    """Request in the batch queue."""
    id: str
    payload: MonitorPayload
    timestamp: int
    retries: int = 0
    priority: str = "normal"  # 'low', 'normal', 'high'


@dataclass
class SDKConfig:
    """Configuration for the SDK."""
    apiKey: str = ""
    apiUrl: Optional[str] = None
    batchSize: int = 10
    batchTimeout: int = 5000  # milliseconds
    retries: int = 3
    timeout: int = 20000  # milliseconds
    enableLocalStorage: bool = True
    localStorageKey: str = "olakai-sdk-queue"
    maxLocalStorageSize: int = 1000000  # 1MB
    debug: bool = False
    verbose: bool = False
    sanitize_patterns: Optional[List[Any]] = None
    logger: Optional[logging.Logger] = None