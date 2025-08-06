"""
Storage service for file-based persistence.

This provides an abstraction layer over file operations.
"""
import os
from typing import Optional
from pathlib import Path
from shared import safe_log
from .index import StorageAdapter 

class FileStorageService(StorageAdapter):
    """File-based storage service"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the storage service.
        
        Args:
            base_path: Base directory for storage files. Defaults to current directory.
        """
        self.base_path = Path(base_path if base_path else os.getcwd())
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def get_item(self, key: str) -> Optional[str]:
        """
        Get an item from storage.
        
        Args:
            key: Storage key
            
        Returns:
            Stored value as string, or None if not found
        """
        try:
            file_path = self.base_path / f"{key}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        except Exception as err:
            safe_log('debug', f"Failed to get item '{key}': {err}")
            return None
    
    def set_item(self, key: str, value: str) -> None:
        """
        Set an item in storage.
        
        Args:
            key: Storage key
            value: Value to store as string
        """
        try:
            file_path = self.base_path / f"{key}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(value)
        except Exception as err:
            safe_log('debug', f"Failed to set item '{key}': {err}")
    
    def remove_item(self, key: str) -> None:
        """
        Remove an item from storage.
        
        Args:
            key: Storage key to remove
        """
        try:
            file_path = self.base_path / f"{key}.json"
            if file_path.exists():
                file_path.unlink()
        except Exception as err:
            safe_log('debug', f"Failed to remove item '{key}': {err}")
    
    def clear(self) -> None:
        """Clear all items from storage."""
        try:
            for file_path in self.base_path.glob("*.json"):
                file_path.unlink()
        except Exception as err:
            safe_log('debug', f"Failed to clear storage: {err}")