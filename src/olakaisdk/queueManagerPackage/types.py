"""
Types specific to the storage system.
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Protocol, Optional
from ..client.types import MonitorPayload, SDKConfig

@dataclass
class BatchRequest:
    """A batch request that can contain multiple payloads."""
    id: str
    payload: List[MonitorPayload]
    timestamp: int
    retries: int = 0
    priority: str = "normal"  # 'low', 'normal', 'high'

@dataclass 
class MonitoringAPIResponse:
    """Response from the monitoring API."""
    success: bool
    results: Optional[List['APIResult']] = None

@dataclass
class APIResult:
    """Individual result from API response."""
    success: bool
    index: int
    error: Optional[str] = None

@dataclass
class StorageConfig:
    """Configuration for storage operations."""
    enabled: bool = True
    storage_key: str = "olakai-sdk-queue"
    max_size: int = 1000000  # 1MB
    file_path: Optional[str] = None

class StorageType(Enum):
    """Type of storage to use."""
    FILE = "file"
    MEMORY = "memory"
    AUTO = "auto"
    DISABLED = "disabled"

class QueueDependencies(Protocol):
    """Dependencies that the queue manager needs from the client."""
    
    def get_config(self) -> SDKConfig:
        """Get the current SDK configuration."""
        ...
    
    def is_online(self) -> bool:
        """Check if the client is online."""
        ...
    
    async def send_with_retry(self, payloads: List[MonitorPayload], max_retries: Optional[int] = None) -> MonitoringAPIResponse:
        """Send payloads with retry logic."""
        ... 