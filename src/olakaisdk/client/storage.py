"""
Local storage management for the Olakai SDK.
"""
import json
from typing import List
from .types import BatchRequest
from ..shared.logger import get_default_logger, safe_log
# Import config function to avoid circular dependency
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .types import SDKConfig

QUEUE_FILE = "olakai_sdk_queue.json"

# Global batch queue
batchQueue: List[BatchRequest] = []


async def load_persisted_queue():
    """
    Load the persisted queue from local storage.
    
    Args:
        logger: Optional logger instance
    """
    global batchQueue
    try:
        with open(QUEUE_FILE, "r") as f:
            data = json.load(f)
        batchQueue = [BatchRequest(**item) for item in data]
        safe_log('info', f"Loaded {len(batchQueue)} items from persisted queue")
    except FileNotFoundError:
        safe_log('info', "No persisted queue found, starting fresh")
    except Exception as err:
        safe_log('debug', f"Failed to load persisted queue: {err}")


async def persist_queue():
    """
    Persist the current queue to local storage.
    
    Args:
        logger: Optional logger instance
    """
    from .config import get_config
    config = get_config()
    
    if not config.enableLocalStorage:
        return
    
    try:
        serialized = json.dumps([b.__dict__ for b in batchQueue])
        if len(serialized) > config.maxLocalStorageSize:
            target_size = int(config.maxLocalStorageSize * 0.8)
            while len(json.dumps([b.__dict__ for b in batchQueue])) > target_size and batchQueue:
                batchQueue.pop(0)
        
        with open(QUEUE_FILE, "w") as f:
            json.dump([b.__dict__ for b in batchQueue], f)
        safe_log('info', "Persisted queue to file")
    except Exception as err:
        safe_log('debug', f"Failed to persist queue: {err}")


def get_batch_queue() -> List[BatchRequest]:
    """Get the current batch queue."""
    return batchQueue


def clear_batch_queue():
    """Clear the batch queue."""
    global batchQueue
    batchQueue = [] 
    logger = get_default_logger()
    safe_log(logger, 'info', "Batch queue cleared")

def add_to_batch_queue(batch_item: BatchRequest):
    """Add an item to the batch queue."""
    global batchQueue
    batchQueue.append(batch_item)
    persist_queue()