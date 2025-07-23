"""
API communication module for the Olakai SDK.
"""
import time
from dataclasses import asdict
from typing import List, Union, Literal

import requests
from .storage import add_to_batch_queue, get_batch_queue
from .types import MonitorPayload, ControlPayload, BatchRequest
from .config import get_config
from ..shared.types import APIResponse, ControlResponse
from ..shared.logger import safe_log
from ..shared.utils import sleep

async def make_api_call(
    payload: Union[List[MonitorPayload], ControlPayload],
    call_type: Literal["monitoring", "control"] = "monitoring",
) -> Union[APIResponse, ControlResponse]:
    """Make API call with optional logging."""
    config = get_config()

    if not config.apiKey:
        raise Exception("[Olakai SDK] API key is not set")
    
    if call_type == "monitoring":
        assert isinstance(payload, MonitorPayload) or isinstance(payload, List[MonitorPayload])
        if not config.monitoringUrl:
            raise Exception("[Olakai SDK] Monitoring URL is not set")
    else:
        assert isinstance(payload, ControlPayload)
        if not config.controlUrl:
            raise Exception("[Olakai SDK] Control URL is not set")

    headers = {"x-api-key": config.apiKey}
    data_dicts = [asdict(x) for x in payload] if call_type == "monitoring" else asdict(payload)
    
    if call_type == "monitoring":
        # Clean up None values
        for data_dict in data_dicts:
            if "errorMessage" in data_dict and data_dict["errorMessage"] is None:
                del data_dict["errorMessage"]
            if "task" in data_dict and data_dict["task"] is None:
                del data_dict["task"]
            if "subTask" in data_dict and data_dict["subTask"] is None:
                del data_dict["subTask"]
    else:
        if ("askedOverrides" in data_dicts and 
            data_dicts["askedOverrides"] is None):
            del data_dicts["askedOverrides"]

    try:
        response = requests.post(
            config.monitoringUrl if call_type == "monitoring" else config.controlUrl,
            json=data_dicts,
            headers=headers,
            timeout=config.timeout / 1000
        )
        safe_log('info', f"Payload: {data_dicts}")
        safe_log('debug', f"Call type: {call_type}, API response: {response}")
        response.raise_for_status()
        result = response.json()

        if call_type == "monitoring":
            return APIResponse(result)
        else:
            return ControlResponse(result)

    except Exception as err:
        raise err


async def send_with_retry(
    payload: Union[List[MonitorPayload], ControlPayload],
    call_type: Literal["monitoring", "control"] = "monitoring",
) -> Union[APIResponse, ControlResponse]:
    """Send payload with retry logic and optional logging."""

    config = get_config()
    max_retries = config.retries if config.retries > 0 else 0
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            result = await make_api_call(payload, call_type)
            safe_log('debug', f"API call successful")
            return result
        except Exception as err:
            last_error = err

            safe_log('debug', f"Attempt {attempt+1}/{max_retries+1} failed: {err}")

            if attempt < max_retries:
                delay = min(1000 * (2 ** attempt), 30000)
                await sleep(delay)
    
    safe_log('debug', f"All retry attempts failed: {last_error}")
    raise last_error


async def send_to_api(
    payload: Union[MonitorPayload, ControlPayload], 
    options: dict = {}, 
):
    """Send payload to API with optional logging."""

    config = get_config()

    if not config.apiKey:
        safe_log('debug', "API key is not set.")
        return
    
    if isinstance(payload, MonitorPayload):
        if config.isBatchingEnabled:
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
            response = await make_api_call([payload], "monitoring")
            # Log any batch-style response information if present
            if (response.totalRequests != None and response.successCount != None):
                safe_log('info', f"Direct API call result: {response.successCount}/{response.totalRequests} requests succeeded")
                if response.failureCount and response.failureCount > 0:
                    safe_log('warning', f"Direct API call result: {response.failureCount}/{response.totalRequests} requests failed")
    
    else:
        await send_with_retry(payload, "control")


from .batch import (
    process_batch_queue,
    schedule_batch_processing
)