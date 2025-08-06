import os
from typing import Optional
from ...client import StorageType, SDKConfig
from ..types import StorageAdapter
from ...shared import safe_log


from .memoryStorage import MemoryStorageService
from .fileStorage import FileStorageService
from .noOpStorage import NoOpStorageService


def is_read_only_env() -> bool:
    """
    Check if the environment is read-only by attempting to create and write to a temporary file.
    """
    import tempfile

    try:
        # Try to create a temporary file to test write permissions
        with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
            tmp_file.write(b"test")
            tmp_file.flush()
        return False  # Successfully wrote, so not read-only
    except (OSError, IOError, PermissionError):
        # If we can't create/write to temp file, try current directory
        try:
            test_file_path = os.path.join(os.getcwd(), ".olakai_write_test")
            with open(test_file_path, "w") as test_file:
                test_file.write("test")
            os.remove(test_file_path)  # Clean up
            return False  # Successfully wrote, so not read-only
        except (OSError, IOError, PermissionError):
            return True  # Cannot write anywhere, environment is read-only


def create_storage_instance(storage_type: StorageType) -> StorageType:
    """
    Create a storage instance based on the environment.
    """
    if storage_type == StorageType.AUTO:
        if is_read_only_env():
            return StorageType.MEMORY
        return StorageType.FILE
    if storage_type == StorageType.MEMORY:
        return StorageType.MEMORY

    elif storage_type == StorageType.FILE:
        if is_read_only_env():
            safe_log(
                "warning", "Environment is read-only, using memory storage"
            )
            return StorageType.MEMORY
        return StorageType.FILE

    elif storage_type == StorageType.DISABLED:
        return StorageType.DISABLED


# Global storage instance
_storage_instance: Optional[StorageAdapter] = None


def init_storage(
    storage_type: StorageType, storage_file_path: Optional[str] = None
) -> None:
    """Initialize the storage instance."""
    global _storage_instance
    _storage_instance_type = create_storage_instance(storage_type)
    if _storage_instance_type == StorageType.MEMORY:
        _storage_instance = MemoryStorageService()
    elif _storage_instance_type == StorageType.FILE:
        _storage_instance = FileStorageService(storage_file_path)
    elif _storage_instance_type == StorageType.DISABLED:
        _storage_instance = NoOpStorageService()


def get_storage() -> StorageAdapter:
    """Get the global storage instance."""
    global _storage_instance
    if _storage_instance is None:
        init_storage(StorageType.AUTO)
    return _storage_instance


def is_storage_enabled(config: SDKConfig) -> bool:
    """Check if storage is enabled in the configuration."""
    return config.enableStorage


def get_storage_key(config: SDKConfig) -> str:
    """Get the storage key from configuration."""
    return config.storageFilePath


def get_max_storage_size(config: SDKConfig) -> int:
    """Get the maximum storage size from configuration."""
    return config.maxStorageSize
