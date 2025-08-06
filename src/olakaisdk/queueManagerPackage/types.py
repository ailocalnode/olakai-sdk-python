"""
Types specific to the storage system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union, Callable
from ..shared import APIResponse, ControlResponse
from ..client import MonitorPayload, SDKConfig


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
