import json
import os
import threading
import time
import logging
from dataclasses import asdict
from typing import Optional, List, Union
import requests

from .types import SDKConfig, MonitorPayload, BatchRequest, APIResponse
from .logger import get_default_logger, safe_log

# Default config
isBatchingEnabled = False

config = SDKConfig(
    apiKey="",
    apiUrl="",
)

batchQueue: List[BatchRequest] = []
batchTimer: Optional[threading.Timer] = None
isOnline = True  # No browser events; assume online

QUEUE_FILE = "olakai_sdk_queue.json"

async def init_client(api_key: str, domain: str = "app.olakai.ai", sdk_config: Optional[SDKConfig] = None, logger: Optional[logging.Logger] = None):
    """
    Initialize the Olakai SDK client.
    
    Args:
        api_key: Your Olakai API key
        domain: API domain (default: app.olakai.ai)
        sdk_config: Optional SDK configuration
        logger: Optional logger instance for logging SDK operations
    """
    global config
    if logger is None:
        logger = await get_default_logger()
    
    config.apiKey = api_key
    config.apiUrl = f"{domain}/api/monitoring/prompt" if domain else "https://staging.app.olakai.ai/api/monitoring/prompt"
    if sdk_config:
        for field_name, value in sdk_config.__dict__.items():
            setattr(config, field_name, value)
    
    await safe_log(logger, 'info', f"Initialized Olakai SDK client with config: {config}")
    
    # Load persisted queue
    if config.enableLocalStorage:
        try:
            if os.path.exists(QUEUE_FILE):
                with open(QUEUE_FILE, "r") as f:
                    parsed_queue = json.load(f)
                    for item in parsed_queue:
                        batchQueue.append(BatchRequest(**item))
                await safe_log(logger, 'debug', f"Loaded {len(parsed_queue)} items from file")
        except Exception as err:
            await safe_log(logger, 'debug', f"Failed to load from file: {err}")
    if batchQueue and isOnline:
        await safe_log(logger, 'info', "Starting batch processing")
        await process_batch_queue(logger=logger)

async def get_config() -> SDKConfig:
    if not config:
        raise Exception("[Olakai SDK] Config is not initialized")
    return config

async def persist_queue(logger: Optional[logging.Logger] = None):
    """
    Persist the current queue to local storage.
    
    Args:
        logger: Optional logger instance
    """
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

async def sleep(ms: int, logger: Optional[logging.Logger] = None):
    """Sleep for specified milliseconds with optional logging."""
    if logger is None:
        logger = await get_default_logger()
    await safe_log(logger, 'info', f"[Olakai SDK] Sleeping for {ms} ms")
    time.sleep(ms / 1000)

async def make_api_call(payload: Union[MonitorPayload, List[MonitorPayload]], logger: Optional[logging.Logger] = None) -> APIResponse:
    """Make API call with optional logging."""
    if logger is None:
        logger = await get_default_logger()
        
    if not config.apiKey:
        raise Exception("[Olakai SDK] API key is not set")
    if not config.apiUrl:
        raise Exception("[Olakai SDK] API URL is not set")

    headers = {"x-api-key": config.apiKey}
    data = {"batch": payload} if isinstance(payload, list) else payload
    data_dict = asdict(data) if isinstance(data, MonitorPayload) else data

    if "errorMessage" in data_dict and data_dict["errorMessage"] is None:
        del data_dict["errorMessage"]

    try:
        response = requests.post(
            config.apiUrl,
            headers=headers,
            json=json.dumps(data_dict),
            timeout=config.timeout / 1000,
        )
        await safe_log(logger, 'info', f"[Olakai SDK] Payload: {data_dict}")
        await safe_log(logger, 'debug', f"[Olakai SDK] API response: {response}")
        response.raise_for_status()
        result = response.json()
        return APIResponse(success=True, data=result)

    except Exception as err:
        raise err

async def send_with_retry(payload: Union[MonitorPayload, List[MonitorPayload]], logger: Optional[logging.Logger] = None) -> bool:
    """Send payload with retry logic and optional logging."""

    if logger is None:
        logger = await get_default_logger()
        
    if config.retries <= 0:
        return (await make_api_call(payload, logger=logger)).success
    else:
        max_retries = config.retries
    last_error = None

    for attempt in range(config.retries + 1):
        try:
            await make_api_call(payload, logger=logger)
            return True
        except Exception as err:
            last_error = err
            await safe_log(logger, 'debug', f"[Olakai SDK] Attempt {attempt+1}/{max_retries+1} failed: {err}")
            if attempt < max_retries:
                delay = min(1000 * (2 ** attempt), 30000)
                await sleep(delay, logger=logger)
    if config.onError and last_error:
        config.onError(last_error)
    await safe_log(logger, 'debug', f"[Olakai SDK] All retry attempts failed: {last_error}")
    return False

async def schedule_batch_processing(logger: Optional[logging.Logger] = None):
    """Schedule batch processing with optional logging."""
    global batchTimer
    if batchTimer:
        return
    
    async def process_with_logger():
        await process_batch_queue(logger=logger)
    
    batchTimer = threading.Timer(config.batchTimeout / 1000, process_with_logger)
    batchTimer.start()

async def process_batch_queue(logger: Optional[logging.Logger] = None):
    """Process the current batch queue with optional logging."""
    global batchTimer
    if logger is None:
        logger = await get_default_logger()
        
    if batchTimer:
        batchTimer.cancel()
        batchTimer = None
    if not batchQueue or not isOnline:
        return
    # Sort by priority
    priority_order = {"high": 0, "normal": 1, "low": 2}
    batchQueue.sort(key=lambda x: priority_order.get(x.priority, 1))
    # Group into batches
    batches = [batchQueue[i:i+config.batchSize] for i in range(0, len(batchQueue), config.batchSize)]
    successful_batches = set()
    for batch_index, batch in enumerate(batches):
        payloads = [item.payload for item in batch]
        try:
            success = send_with_retry(payloads, logger=logger)
            if success:
                successful_batches.add(batch_index)
                await safe_log(logger, 'debug', f"[Olakai SDK] Successfully sent batch of {len(batch)} items")
        except Exception as err:
            await safe_log(logger, 'debug', f"[Olakai SDK] Batch {batch_index} failed: {err}")
    # Remove successfully sent items
    remove_count = 0
    for i in range(len(batches)):
        if i in successful_batches:
            remove_count += len(batches[i])
        else:
            break
    if remove_count > 0:
        del batchQueue[:remove_count]
        await persist_queue(logger=logger)
    if batchQueue:
        await schedule_batch_processing(logger=logger)

async def send_to_api(payload: MonitorPayload, options: dict = {}, logger: Optional[logging.Logger] = None):
    """Send payload to API with optional logging."""
    if logger is None:
        logger = await get_default_logger()
        
    if not config.apiKey:
        await safe_log(logger, 'debug', "[Olakai SDK] API key is not set.")
        return
    if isBatchingEnabled:
        batch_item = BatchRequest(
            id=f"{int(time.time() * 1000)}",
            payload=payload,
            timestamp=int(time.time() * 1000),
            retries=0,
            priority=options.get("priority", "normal"),
        )
        batchQueue.append(batch_item)
        await persist_queue(logger=logger)
        if len(batchQueue) >= config.batchSize or options.get("priority") == "high":
            await process_batch_queue(logger=logger)
        else:
            await schedule_batch_processing(logger=logger)
    else:
        await make_api_call(payload, logger=logger)

async def get_queue_size() -> int:
    return len(batchQueue)

async def clear_queue(logger: Optional[logging.Logger] = None):
    """Clear the queue with optional logging."""
    global batchQueue
    if logger is None:
        logger = await get_default_logger()
        
    batchQueue = []
    if config.enableLocalStorage and os.path.exists(QUEUE_FILE):
        os.remove(QUEUE_FILE)
        await safe_log(logger, 'info', "[Olakai SDK] Cleared queue from file")

async def flush_queue(logger: Optional[logging.Logger] = None):
    """Flush the queue with optional logging."""
    if logger is None:
        logger = await get_default_logger()
        
    await safe_log(logger, 'info', "[Olakai SDK] Flushing queue")
    await process_batch_queue(logger=logger) 