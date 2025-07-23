
from abc import ABC, abstractmethod
from typing import Optional


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


# Global storage instance
_storage_instance: Optional[StorageAdapter] = None

def get_storage() -> StorageAdapter:
    """Get the global storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = StorageService()
    return _storage_instance

def is_storage_enabled(config: SDKConfig) -> bool:
    """Check if storage is enabled in the configuration."""
    return config.enableLocalStorage

def get_storage_key(config: SDKConfig) -> str:
    """Get the storage key from configuration."""
    return config.localStorageKey

def get_max_storage_size(config: SDKConfig) -> int:
    """Get the maximum storage size from configuration."""
    return config.maxLocalStorageSize 