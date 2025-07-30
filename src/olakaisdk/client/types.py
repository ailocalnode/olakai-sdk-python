"""
Types specific to client functionality (API communication, batching, configuration).
"""
from dataclasses import dataclass
from typing import Optional, List, Any
import logging
from enum import Enum

@dataclass
class MonitorPayload:
    """Payload for monitoring data sent to API."""
    email: str
    chatId: str
    prompt: str
    response: str
    blocked: Optional[bool] = False
    tokens: Optional[int] = 0
    requestTime: Optional[int] = 0
    task: Optional[str] = None
    subTask: Optional[str] = None
    errorMessage: Optional[str] = None
    sensitivity: Optional[List[str]] = None

@dataclass
class ControlPayload:
    """Payload for control data sent to API."""
    prompt: str = ""
    email: Optional[str] = "anonymous@olakai.ai"
    chatId: Optional[str] = "123"
    task: Optional[str] = None
    subTask: Optional[str] = None
    tokens: Optional[int] = 0
    overrideControlCriteria: Optional[List[str]] = None

@dataclass
class BatchRequest:
    """Request in the batch queue."""
    id: str
    payload: List[MonitorPayload]
    timestamp: int
    retries: int = 0
    priority: str = "normal"  # 'low', 'normal', 'high'

class StorageType(Enum):
    """Type of storage to use."""
    FILE = "file"
    MEMORY = "memory"
    AUTO = "auto"
    DISABLED = "disabled"

@dataclass
class SDKConfig:
    """Configuration for the SDK."""
    apiKey: str = ""
    monitoringUrl: Optional[str] = None
    controlUrl: Optional[str] = None
    isBatchingEnabled: bool = False
    batchSize: int = 10
    batchTimeout: int = 5000  # milliseconds
    retries: int = 3
    timeout: int = 20000  # milliseconds
    enableStorage: bool = True
    storageType: StorageType = StorageType.AUTO
    maxStorageSize: int = 1000000  # 1MB
    storageFilePath: Optional[str] = None
    debug: bool = False
    verbose: bool = False
    sanitize_patterns: Optional[List[Any]] = None
    logger: Optional[logging.Logger] = None