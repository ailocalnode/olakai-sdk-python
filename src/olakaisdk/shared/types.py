"""
Common types used across the SDK.
"""

from abc import ABC, abstractmethod

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Any, Callable, Union, Dict
from logging import Logger
from enum import Enum
import json

JSONType = Union[
    None, bool, int, float, str,
    Dict[str, "JSONType"],
    List["JSONType"]
]

@dataclass
class SanitizePattern:
    pattern: Optional[str] = None
    key: Optional[str] = None
    replacement: Optional[str] = None   

@dataclass
class Middleware:
    """Middleware for monitoring functions."""

    name: str
    before_call: Optional[Callable] = None
    after_call: Optional[Callable] = None
    on_error: Optional[Callable] = None


@dataclass
class MonitorUtils:
    """Utility functions for data capture in monitoring."""

    @staticmethod
    def capture_all_f(**kwargs):
        """Capture all input and output data."""
        return {
            "input": str(kwargs["args"]) + json.dumps(kwargs["kwargs"]),
            "output": kwargs["result"],
        }

    @staticmethod
    def capture_input_f(**kwargs):
        """Capture only input data."""
        return {
            "input": str(kwargs["args"]) + json.dumps(kwargs["kwargs"]),
            "output": "Function executed successfully",
        }

    @staticmethod
    def capture_output_f(**kwargs):
        """Capture only output data."""
        return {"input": "Function called", "output": kwargs["result"]}


@dataclass
class MonitorOptions:
    """Options for monitoring functions."""

    capture: Optional[Callable] = (
        MonitorUtils.capture_all_f
    )  # Will be set to default in helpers.py
    sanitize: bool = False
    send_on_function_error: bool = True
    priority: str = "normal"
    email: Optional[Union[str, Callable]] = "anonymous@olakai.ai"
    chatId: Optional[Union[str, Callable]] = "123"
    task: Optional[str] = None
    subTask: Optional[str] = None
    overrideControlCriteria: Optional[List[str]] = None


@dataclass
class MonitorPayload:
    """Payload for monitoring data sent to API."""

    email: str
    chatId: str
    prompt: JSONType
    response: JSONType
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

    prompt: JSONType
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
    batchTimeout: int = 300  # milliseconds
    retries: int = 3
    timeout: int = 20000  # milliseconds
    enableStorage: bool = True
    storageType: StorageType = StorageType.MEMORY
    maxStorageSize: int = 1000000  # 1MB
    storageFilePath: Optional[str] = None
    debug: bool = False
    verbose: bool = False
    sanitize_patterns: Optional[List[SanitizePattern]] = None
    logger: Optional[Logger] = None


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


class StorageAdapter(ABC):
    @abstractmethod
    def get_item(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set_item(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def remove_item(self, key: str) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


@dataclass
class StorageConfig:
    """Configuration for storage operations."""

    enabled: bool = True
    storage_key: str = "olakai-sdk-queue"
    max_size: int = 1000000  # 1MB
    file_path: Optional[str] = None


class QueueDependencies:
    """Dependencies that the queue manager needs from the client."""

    def __init__(
        self,
        config: SDKConfig,
        send_with_retry: Callable[
            [List[MonitorPayload], Optional[int]],
            Union[APIResponse, ControlResponse],
        ],
    ):
        self.config = config
        self.send_with_retry = send_with_retry

    def get_config(self) -> SDKConfig:
        """Get the current SDK configuration."""
        return self.config

    def is_online(self) -> bool:
        """Check if the client is online."""
        ...

    async def send_with_retry(
        self, payloads: List[MonitorPayload], max_retries: Optional[int] = None
    ) -> Union[APIResponse, ControlResponse]:
        """Send payloads with retry logic."""
        return self.send_with_retry(payloads, max_retries)



class StorageAdapter(ABC):
    @abstractmethod
    def get_item(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set_item(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def remove_item(self, key: str) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


@dataclass
class StorageConfig:
    """Configuration for storage operations."""

    enabled: bool = True
    storage_key: str = "olakai-sdk-queue"
    max_size: int = 1000000  # 1MB
    file_path: Optional[str] = None


class QueueDependencies:
    """Dependencies that the queue manager needs from the client."""

    def __init__(
        self,
        config: SDKConfig,
        send_with_retry: Callable[
            [List[MonitorPayload], Optional[int]],
            Union[APIResponse, ControlResponse],
        ],
    ):
        self.config = config
        self.send_with_retry = send_with_retry

    def get_config(self) -> SDKConfig:
        """Get the current SDK configuration."""
        return self.config

    def is_online(self) -> bool:
        """Check if the client is online."""
        ...

    async def send_with_retry(
        self, payloads: List[MonitorPayload], max_retries: Optional[int] = None
    ) -> Union[APIResponse, ControlResponse]:
        """Send payloads with retry logic."""
        return self.send_with_retry(payloads, max_retries)
