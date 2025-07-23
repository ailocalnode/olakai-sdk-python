from .index import StorageAdapter


class NoOpStorageService(StorageAdapter):
    """
    No-op storage service that does nothing
    """

    def get_item(self, key: str) -> None:
        return None
    
    def set_item(self, key: str, value: str) -> None:
        pass
    
    def remove_item(self, key: str) -> None:
        pass
    
    def clear(self) -> None:
        pass