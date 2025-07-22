"""
Local storage management for the Olakai SDK.
"""
import json
import logging
from typing import Optional, List
from .types import BatchRequest
from ..shared.logger import get_default_logger, safe_log
# Import config function to avoid circular dependency
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .types import SDKConfig

QUEUE_FILE = "olakai_sdk_queue.json"

# Global batch queue
batchQueue: List[BatchRequest] = []


async def load_persisted_queue(logger: Optional[logging.Logger] = None):
    """
    Load the persisted queue from local storage.
    
    Args:
        logger: Optional logger instance
    """
    global batchQueue
    if logger is None:
        logger = await get_default_logger()
    
    try:
        with open(QUEUE_FILE, "r") as f:
            data = json.load(f)
        batchQueue = [BatchRequest(**item) for item in data]
        await safe_log(logger, 'info', f"Loaded {len(batchQueue)} items from persisted queue")
    except FileNotFoundError:
        await safe_log(logger, 'info', "No persisted queue found, starting fresh")
    except Exception as err:
        await safe_log(logger, 'debug', f"Failed to load persisted queue: {err}")


async def persist_queue(logger: Optional[logging.Logger] = None):
    """
    Persist the current queue to local storage.
    
    Args:
        logger: Optional logger instance
    """
    from .config import get_config
    config = await get_config()
    
    if not config.enableLocalStorage:
        return
    
    if logger is None:
        logger = await get_default_logger()
    
    try:
        serialized = json.dumps([b.__dict__ for b in batchQueue])
        if len(serialized) > config.maxLocalStorageSize:
            target_size = int(config.maxLocalStorageSize * 0.8)
            while len(json.dumps([b.__dict__ for b in batchQueue])) > target_size and batchQueue:
                batchQueue.pop(0)
        
        with open(QUEUE_FILE, "w") as f:
            json.dump([b.__dict__ for b in batchQueue], f)
        await safe_log(logger, 'info', "Persisted queue to file")
    except Exception as err:
        await safe_log(logger, 'debug', f"Failed to persist queue: {err}")


def get_batch_queue() -> List[BatchRequest]:
    """Get the current batch queue."""
    return batchQueue


def clear_batch_queue():
    """Clear the batch queue."""
    global batchQueue
    batchQueue = [] 