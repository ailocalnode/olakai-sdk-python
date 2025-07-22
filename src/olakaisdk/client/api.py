"""
API communication module for the Olakai SDK.
"""
import time
from dataclasses import asdict
from typing import List, Union

import requests
from .storage import add_to_batch_queue, get_batch_queue
from .types import MonitorPayload, ControlPayload, BatchRequest
from .config import get_config
from ..shared.types import APIResponse, ControlResponse
from ..shared.logger import safe_log
from ..shared.utils import sleep

isBatchingEnabled = False


async def make_api_call(
    payload: Union[MonitorPayload, List[MonitorPayload]], 
) -> APIResponse:
    """Make API call with optional logging."""
    config = get_config()
    
    if not config.apiKey:
        raise Exception("[Olakai SDK] API key is not set")
    if not config.apiUrl:
        raise Exception("[Olakai SDK] API URL is not set")

    headers = {"x-api-key": config.apiKey}
    data_dicts = (
        [asdict(x) for x in payload] 
        if isinstance(payload, list) 
        else [asdict(payload)]
    )
    
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
        safe_log('info', f"Payload: {data_dicts}")
        safe_log('debug', f"API response: {response}")
        response.raise_for_status()
        result = response.json()
        return APIResponse(success=True, data=result)

    except Exception as err:
        raise err


async def send_with_retry(
    payload: Union[MonitorPayload, List[MonitorPayload]], 
) -> bool:
    """Send payload with retry logic and optional logging."""

    config = get_config()
    max_retries = config.retries if config.retries > 0 else 0
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            await make_api_call(payload)
            return True
        except Exception as err:
            last_error = err

            safe_log('debug', f"Attempt {attempt+1}/{max_retries+1} failed: {err}")

            if attempt < max_retries:
                delay = min(1000 * (2 ** attempt), 30000)
                await sleep(delay)
    
    safe_log('debug', f"All retry attempts failed: {last_error}")
    return False


async def send_to_api(
    payload: MonitorPayload, 
    options: dict = {}, 
):
    """Send payload to API with optional logging."""

    config = get_config()

    if not config.apiKey:
        safe_log('debug', "API key is not set.")
        return
    
    if isBatchingEnabled:
        batch_item = BatchRequest(
            id=f"{int(time.time() * 1000)}",
            payload=payload,
            timestamp=int(time.time() * 1000),
            retries=0,
            priority=options.get("priority", "normal"),
        )
        add_to_batch_queue(batch_item)
        if (len(get_batch_queue()) >= config.batchSize or 
            options.get("priority") == "high"):
            await process_batch_queue()
        else:
            await schedule_batch_processing()
    else:
        await make_api_call(payload)


async def call_control_api(
    payload: ControlPayload, 
) -> ControlResponse:
    """Send payload to control API with optional logging."""
    config = get_config()

    if not config.apiKey:
        raise Exception("[Olakai SDK] API key is not set")
    if not config.apiUrl:
        raise Exception("[Olakai SDK] API URL is not set")

    headers = {"x-api-key": config.apiKey}
    data_dict = asdict(payload)

    if ("askedOverrides" in data_dict and 
        data_dict["askedOverrides"] is None):
        del data_dict["askedOverrides"]

    try:
        response = requests.post(
            config.apiUrl,
            json=data_dict,
            headers=headers,
            timeout=config.timeout / 1000
        )
        safe_log('info', f"Payload: {data_dict}")
        safe_log('debug', f"API response: {response}")
        response.raise_for_status()
        result = response.json()
        return ControlResponse(success=True, data=result)
    except Exception as err:
        raise err
    

from .batch import (
    process_batch_queue,
    schedule_batch_processing
)