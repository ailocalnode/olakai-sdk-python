"""
Types specific to the storage system.
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Protocol, Optional, Union
from ..shared.types import APIResponse, ControlResponse


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
    
    async def send_with_retry(self, payloads: List[MonitorPayload], max_retries: Optional[int] = None) -> Union[APIResponse, ControlResponse]:
        """Send payloads with retry logic."""
        ... 

from ..client.types import MonitorPayload, SDKConfig