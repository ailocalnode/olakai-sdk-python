"""
Batch processing management for the Olakai SDK.
"""
import threading

from typing import Optional
from .storage import get_batch_queue, clear_batch_queue, persist_queue
from .config import get_config
from .api import send_with_retry
from ..shared.logger import safe_log

# Global state
batchTimer: Optional[threading.Timer] = None
isOnline = True  # No browser events; assume online


async def get_queue_size() -> int:
    """Get the current size of the batch queue."""
    return len(get_batch_queue())


async def clear_queue():
    """Clear the batch queue."""
    clear_batch_queue()


async def flush_queue():
    """Force flush the batch queue."""
    await process_batch_queue()


async def schedule_batch_processing():
    """Schedule batch processing with optional logging."""
    global batchTimer
    if batchTimer:
        return
    
    config = get_config()
    
    async def process_with_logger():
        await process_batch_queue()
    
    batchTimer = threading.Timer(config.batchTimeout / 1000, process_with_logger)
    batchTimer.start()


async def process_batch_queue():
    """Process the current batch queue with optional logging."""
    global batchTimer
    if batchTimer:
        batchTimer.cancel()
        batchTimer = None
    
    batch_queue = get_batch_queue()
    if not batch_queue or not isOnline:
        return
    
    config = get_config()
    
    # Sort by priority (high > normal > low)
    priority_order = {"high": 3, "normal": 2, "low": 1}
    batch_queue.sort(key=lambda x: priority_order.get(x.priority, 2), reverse=True)
    
    # Process in batches
    batch_size = min(config.batchSize, len(batch_queue))
    current_batch = batch_queue[:batch_size]
    
    if current_batch:
        try:
            payloads = [req.payload for req in current_batch]
            success = await send_with_retry(payloads)
            
            if success:
                # Remove successful items from queue
                for _ in range(len(current_batch)):
                    batch_queue.pop(0)
                safe_log('info', f"Successfully sent batch of {len(current_batch)} items")
            else:
                # Increment retry count for failed items
                for req in current_batch:
                    req.retries += 1
                    if req.retries >= config.retries:
                        batch_queue.remove(req)
                        safe_log('debug', f"Dropped request after {config.retries} failed attempts")
                        
        except Exception as error:
            safe_log('error', f"Batch processing failed: {error}")
    
    # Persist updated queue
    await persist_queue()
    
    # Schedule next batch if queue is not empty
    if batch_queue:
        await schedule_batch_processing() 