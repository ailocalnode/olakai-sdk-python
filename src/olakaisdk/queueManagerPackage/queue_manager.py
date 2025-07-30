"""
Queue Manager - Handles all queue operations and state.

This is a Python implementation of the TypeScript QueueManager with similar functionality.
"""
import json
import asyncio
import time
from typing import List, Optional
from .storage.index import get_storage, is_storage_enabled, get_storage_key, get_max_storage_size
from ..client.types import MonitorPayload, BatchRequest
from ..shared.logger import safe_log
from .types import QueueDependencies
from ..shared.exceptions import QueueNotInitializedError
from ..shared.utils import sleep, fire_and_forget


class QueueManager:
    """Queue Manager - Handles all queue operations and state."""
    
    def __init__(self, dependencies: QueueDependencies):
        """
        Initialize the queue manager.
        
        Args:
            dependencies: Dependencies needed from the client
        """
        self.dependencies = dependencies
        self.batch_queue: List[BatchRequest] = []
        self.batch_timer: Optional[asyncio.Task] = None
        self.clear_retries_timer: Optional[asyncio.Task] = None
        
    def initialize(self) -> None:
        """Initialize the queue by loading persisted data."""
        config = self.dependencies.get_config()
        
        if is_storage_enabled(config):
            try:
                storage = get_storage()
                stored = storage.get_item(get_storage_key(config))
                if stored:
                    parsed_queue = json.loads(stored)
                    self.batch_queue = [
                        BatchRequest(
                            id=item['id'],
                            payload=[MonitorPayload(**p) for p in item['payload']],
                            timestamp=item['timestamp'],
                            retries=item.get('retries', 0),
                            priority=item.get('priority', 'normal')
                        )
                        for item in parsed_queue
                    ]
                    safe_log('info', f"Loaded {len(parsed_queue)} items from storage")
            except Exception as err:
                safe_log('warning', f"Failed to load from storage: {err}")
        
        # Start processing queue if we have items and we're online
        if self.batch_queue and self.dependencies.is_online():
            safe_log('info', "Starting batch processing")
            self._process_batch_queue()
    
    async def add_to_queue(
        self,
        payload: MonitorPayload,
        retries: int = 0,
        priority: str = "normal"
    ) -> None:
        """
        Add an item to the queue.
        
        Args:
            payload: The payload to add
            retries: Number of retries for this payload
            priority: Priority level ('low', 'normal', 'high')
        """
        config = self.dependencies.get_config()
        
        if len(self.batch_queue) == 0:
            # Create first batch
            self.batch_queue.append(BatchRequest(
                id=f"{int(time.time() * 1000)}-{hash(str(payload)) % 100000}",
                payload=[payload],
                timestamp=int(time.time() * 1000),
                retries=retries,
                priority=priority
            ))
            self._persist_queue()
            self._schedule_batch_processing()
            self._schedule_clear_retries_queue()
            return
        
        # Try to add to existing batch with same retry count and not full
        for batch in reversed(self.batch_queue):
            if (len(batch.payload) < config.batchSize and 
                batch.retries == retries):
                batch.payload.append(payload)
                if priority == "high":
                    batch.priority = "high"
                self._persist_queue()
                if priority == "high":
                    await self._process_batch_queue()
                else:
                    self._schedule_batch_processing()
                self._schedule_clear_retries_queue()
                return
        
        # Create new batch
        self.batch_queue.append(BatchRequest(
            id=f"{int(time.time() * 1000)}-{hash(str(payload)) % 100000}",
            payload=[payload],
            timestamp=int(time.time() * 1000),
            retries=retries,
            priority=priority
        ))
        
        self._persist_queue()
        if priority == "high":
            await self._process_batch_queue()
        else:
            self._schedule_batch_processing()
        self._schedule_clear_retries_queue()
    
    def clear_retries_queue(self) -> None:
        """Clear batches that have exceeded maximum retries."""
        if self.clear_retries_timer:
            self.clear_retries_timer.cancel()
            self.clear_retries_timer = None
        
        config = self.dependencies.get_config()
        original_length = len(self.batch_queue)
        self.batch_queue = [
            batch for batch in self.batch_queue 
            if batch.retries < config.retries
        ]
        
        if len(self.batch_queue) != original_length:
            safe_log('info', f"Removed {original_length - len(self.batch_queue)} batches that exceeded max retries")
            self._persist_queue()
    
    def get_size(self) -> int:
        """Get the current queue size (number of batches)."""
        return len(self.batch_queue)
    
    def clear(self) -> None:
        """Clear the queue without sending."""
        self.batch_queue = []
        config = self.dependencies.get_config()
        if is_storage_enabled(config):
            storage = get_storage()
            storage.remove_item(get_storage_key(config))
            safe_log('info', "Cleared queue from storage")
    
    async def flush(self) -> None:
        """Flush the queue (send all pending items)."""
        safe_log('info', "Flushing queue")
        await self._process_batch_queue()
    
    def _persist_queue(self) -> None:
        """Persist the queue to storage."""
        config = self.dependencies.get_config()
        
        if not is_storage_enabled(config):
            return
        
        try:
            storage = get_storage()
            
            # Convert to serializable format
            serializable_queue = []
            for batch in self.batch_queue:
                serializable_queue.append({
                    'id': batch.id,
                    'payload': [payload.__dict__ for payload in batch.payload],
                    'timestamp': batch.timestamp,
                    'retries': batch.retries,
                    'priority': batch.priority
                })
            
            serialized = json.dumps(serializable_queue)
            max_size = get_max_storage_size(config)
            
            if len(serialized) > max_size:
                # Remove oldest items if queue is too large
                target_size = int(max_size * 0.8)
                while (len(json.dumps(serializable_queue)) > target_size and 
                       serializable_queue):
                    serializable_queue.pop(0)
                    self.batch_queue.pop(0)
            
            storage.set_item(get_storage_key(config), json.dumps(serializable_queue))
            safe_log('info', "Persisted queue to storage")
        except Exception as err:
            safe_log('warn', f"Failed to persist queue: {err}")
    
    def _schedule_batch_processing(self) -> None:
        """Schedule the batch processing."""
        if self.batch_timer:
            return
        
        config = self.dependencies.get_config()
        
        async def process_after_timeout():
            await sleep(config.batchTimeout)  # Convert ms to seconds
            await self._process_batch_queue()
        try:
            self.batch_timer = asyncio.create_task(process_after_timeout())
        except RuntimeError:
            fire_and_forget(process_after_timeout)
    
    def _schedule_clear_retries_queue(self) -> None:
        """Schedule the clear retries queue."""
        if self.clear_retries_timer:
            return
        
        config = self.dependencies.get_config()
        
        async def clear_after_timeout():
            await sleep(config.batchTimeout)  # Convert ms to seconds
            self.clear_retries_queue()
        
        try:
            self.clear_retries_timer = asyncio.create_task(clear_after_timeout())
        except RuntimeError:
            fire_and_forget(clear_after_timeout)
    
    async def _process_batch_queue(self) -> None:
        """Process the batch queue."""
        if self.batch_timer:
            self.batch_timer.cancel()
            self.batch_timer = None
        
        # Sort by priority: high, normal, low
        priority_order = {"high": 0, "normal": 1, "low": 2}
        self.batch_queue.sort(key=lambda b: priority_order.get(b.priority, 1))
        
        # Process one batch at a time
        if not self.batch_queue:
            return
        
        current_batch = self.batch_queue.pop(0)
        self._persist_queue()
        
        payloads = current_batch.payload
        
        if not payloads:
            # Schedule next processing if there are more batches
            if self.batch_queue:
                self._schedule_batch_processing()
            return
        
        try:
            result = await self.dependencies.send_with_retry(payloads)
            
            if result.success:
                # All succeeded
                safe_log('info', f"Batch of {len(current_batch.payload)} items sent successfully")
                self._persist_queue()
            else:
                # Handle partial failures
                safe_log('warning', f"Batch of {len(current_batch.payload)} items failed to send in total")
                
            

                new_batch = BatchRequest(
                    id=f"{int(time.time() * 1000)}-{hash(str(current_batch.id)) % 100000}",
                    payload=[],
                    timestamp=int(time.time() * 1000),
                    retries=current_batch.retries + 1,
                    priority=current_batch.priority
                )
                
                if result.results:
                    for api_result in result.results:
                        if not api_result.success:
                            safe_log('warning', f"Item {payloads[api_result.index]} failed to send")
                            new_batch.payload.append(payloads[api_result.index])
                else:
                    # If no detailed results, retry all payloads
                    new_batch.payload = payloads
                
                if new_batch.payload:
                    self.batch_queue.append(new_batch)
                    self._persist_queue()
            
            # Continue processing if there are more batches
            if self.batch_queue:
                self._schedule_batch_processing()
                
        except Exception as err:
            safe_log('error', f"Batch processing failed: {err}")
            # Re-add payloads with incremented retry count
            for payload in payloads:
                await self.add_to_queue(
                    payload,
                    retries=current_batch.retries + 1,
                    priority=current_batch.priority
                )
            
            # Continue processing
            if self.batch_queue:
                self._schedule_batch_processing()

# Global queue manager instance
_queue_manager: Optional[QueueManager] = None

def init_queue_manager(dependencies: QueueDependencies) -> QueueManager:
    """
    Initialize the queue manager.
    
    Args:
        dependencies: Dependencies needed from the client
        
    Returns:
        The initialized queue manager
    """
    global _queue_manager
    
    if _queue_manager:
        safe_log('warn', "Queue manager already initialized, returning existing instance")
        return _queue_manager
    
    _queue_manager = QueueManager(dependencies)
    _queue_manager.initialize()
    
    safe_log('info', f"Queue manager initialized with {_queue_manager.get_size()} items in queue")
    
    return _queue_manager

def get_queue_manager() -> QueueManager:
    """
    Get the current queue manager instance.
    
    Returns:
        The queue manager instance
        
    Raises:
        QueueNotInitializedError: If queue manager is not initialized
    """
    if not _queue_manager:
        safe_log('warning', '[Olakai SDK] Queue manager not initialized. Call init_queue_manager first.')
        raise QueueNotInitializedError('[Olakai SDK] Queue manager not initialized. Call init_queue_manager first.')
    return _queue_manager

# Public API functions that delegate to the queue manager
def get_queue_size() -> int:
    """Get the current queue size."""
    return get_queue_manager().get_size()

def clear_queue() -> None:
    """Clear the queue without sending."""
    return get_queue_manager().clear()

async def flush_queue() -> None:
    """Flush the queue (send all pending items)."""
    return await get_queue_manager().flush()

async def add_to_queue(
    payload: MonitorPayload,
    retries: int = 0,
    priority: str = "normal"
) -> None:
    """
    Add an item to the queue.
    
    Args:
        payload: The payload to add
        retries: Number of retries for this payload
        priority: Priority level ('low', 'normal', 'high')
    """
    return await get_queue_manager().add_to_queue(payload, retries, priority) 

