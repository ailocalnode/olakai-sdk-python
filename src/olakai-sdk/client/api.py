"""
API communication module for the Olakai SDK.
"""
import time
import logging
from dataclasses import asdict
from typing import Optional, List, Union
import requests
from .types import MonitorPayload
from .config import get_config
from ..shared.types import APIResponse
from ..shared.logger import get_default_logger, safe_log
from .batch import batchQueue, persist_queue, process_batch_queue, schedule_batch_processing
from .types import BatchRequest

isBatchingEnabled = False

async def sleep(ms: int, logger: Optional[logging.Logger] = None):
    """Sleep for specified milliseconds with optional logging."""
    if logger is None:
        logger = get_default_logger()
    safe_log(logger, 'debug', f"Sleeping for {ms}ms")
    time.sleep(ms / 1000)


async def make_api_call(payload: Union[MonitorPayload, List[MonitorPayload]], logger: Optional[logging.Logger] = None) -> APIResponse:
    """Make API call with optional logging."""
    if logger is None:
        logger = get_default_logger()
        
    config = await get_config()
    
    if not config.apiKey:
        raise Exception("[Olakai SDK] API key is not set")
    if not config.apiUrl:
        raise Exception("[Olakai SDK] API URL is not set")

    headers = {"x-api-key": config.apiKey}
    data_dicts = [asdict(x) for x in payload] if isinstance(payload, list) else [asdict(payload)]
    
    # Clean up None values
    for data_dict in data_dicts:
        if "errorMessage" in data_dict and data_dict["errorMessage"] is None:
            del data_dict["errorMessage"]
        if "task" in data_dict and data_dict["task"] is None:
            del data_dict["task"]
        if "subTask" in data_dict and data_dict["subTask"] is None:
            del data_dict["subTask"]

    try:
        response = requests.post(
            config.apiUrl,
            json=data_dicts,
            headers=headers,
            timeout=config.timeout / 1000
        )
        safe_log(logger, 'info', f"[Olakai SDK] Payload: {data_dicts}")
        safe_log(logger, 'debug', f"[Olakai SDK] API response: {response}")
        response.raise_for_status()
        result = response.json()
        return APIResponse(success=True, data=result)

    except Exception as err:
        raise err


async def send_with_retry(payload: Union[MonitorPayload, List[MonitorPayload]], logger: Optional[logging.Logger] = None) -> bool:
    """Send payload with retry logic and optional logging."""
    if logger is None:
        logger = get_default_logger()
        
    config = await get_config()
    max_retries = config.retries if config.retries > 0 else 0
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            await make_api_call(payload, logger=logger)
            return True
        except Exception as err:
            last_error = err
            safe_log(logger, 'debug', f"[Olakai SDK] Attempt {attempt+1}/{max_retries+1} failed: {err}")
            if attempt < max_retries:
                delay = min(1000 * (2 ** attempt), 30000)
                await sleep(delay, logger=logger)
    
    safe_log(logger, 'debug', f"[Olakai SDK] All retry attempts failed: {last_error}")
    return False


async def send_to_api(payload: MonitorPayload, options: dict = {}, logger: Optional[logging.Logger] = None):
    """Send payload to API with optional logging."""
    if logger is None:
        logger = get_default_logger()

    config = await get_config()

    if not config.apiKey:
        safe_log(logger, 'debug', "[Olakai SDK] API key is not set.")
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