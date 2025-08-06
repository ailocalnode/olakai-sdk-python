"""
Storage module for the Olakai SDK queue manager.

This module provides different storage adapters for persisting queue data.
"""

from .memoryStorage import MemoryStorageService
from .fileStorage import FileStorageService
from .noOpStorage import NoOpStorageService
from .index import (
    get_storage,
    is_storage_enabled,
    get_storage_key,
    get_max_storage_size,
)

__all__ = [
    "get_storage",
    "is_storage_enabled",
    "get_storage_key",
    "get_max_storage_size",
    "MemoryStorageService",
    "FileStorageService",
    "NoOpStorageService",
]
