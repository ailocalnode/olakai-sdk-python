from ...shared import StorageAdapter
from typing import Optional


class MemoryStorageService(StorageAdapter):
    """
    Simple memory storage service
    """

    # TODO: Add a max size to the storage
    def __init__(self):
        self.storage = {}

    def get_item(self, key: str) -> Optional[str]:
        return self.storage.get(key) or None

    def set_item(self, key: str, value: str) -> None:
        self.storage[key] = value

    def remove_item(self, key: str) -> None:
        del self.storage[key]

    def clear(self) -> None:
        self.storage.clear()
