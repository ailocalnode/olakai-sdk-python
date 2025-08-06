"""
API communication module for the Olakai SDK.
"""
from dataclasses import asdict
from typing import List, Union, Literal

import requests
from queueManagerPackage import add_to_queue
from .types import MonitorPayload, ControlPayload, SDKConfig
from shared import APIResponse, ControlResponse, ControlDetails
from shared import safe_log
from shared import sleep
from shared import (
    APIKeyMissingError, 
    URLConfigurationError, 
    APITimeoutError, 
    APIResponseError, 
    RetryExhaustedError
)

async def make_api_call(
    config: SDKConfig,
    payload: Union[List[MonitorPayload], ControlPayload],
    call_type: Literal["monitoring", "control"] = "monitoring",
) -> Union[APIResponse, ControlResponse]:
    """Make API call with optional logging."""

    if not config.apiKey:
        raise APIKeyMissingError("[Olakai SDK] API key is not set")
    
    if call_type == "monitoring":
        assert not isinstance(payload, ControlPayload)
        if not config.monitoringUrl:
            raise URLConfigurationError("[Olakai SDK] Monitoring URL is not set")
    else:
        assert isinstance(payload, ControlPayload)
        if not config.controlUrl:
            raise URLConfigurationError("[Olakai SDK] Control URL is not set")

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
        if ("overrideControlCriteria" in data_dicts and 
            data_dicts["overrideControlCriteria"] is None):
            del data_dicts["overrideControlCriteria"]
        if "task" in data_dicts and data_dicts["task"] is None:
            del data_dicts["task"]
        if "subTask" in data_dicts and data_dicts["subTask"] is None:
            del data_dicts["subTask"]

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
        safe_log('debug', f"API response: {result}")

        if call_type == "monitoring":
            return APIResponse(**result)
        else:
            result["details"] = ControlDetails(**result["details"]) 
            return ControlResponse(**result)

    except requests.exceptions.Timeout as err:
        raise APITimeoutError(f"Request timed out after {config.timeout}ms") from err
    except requests.exceptions.HTTPError as err:
        raise APIResponseError(f"HTTP error: {err.response.status_code} - {err.response.text}") from err
    except requests.exceptions.RequestException as err:
        raise APIResponseError(f"Request failed: {str(err)}") from err
    except Exception as err:
        raise APIResponseError(f"Unexpected error during API call: {str(err)}") from err


async def send_with_retry(
    config: SDKConfig,
    payload: Union[List[MonitorPayload], ControlPayload],
    call_type: Literal["monitoring", "control"] = "monitoring",
) -> Union[APIResponse, ControlResponse]:
    """Send payload with retry logic and optional logging."""

    max_retries = config.retries if config.retries > 0 else 0
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            result = await make_api_call(config, payload, call_type)
            safe_log('debug', f"API call successful")
            return result
        except (APITimeoutError, APIResponseError) as err:
            last_error = err

            safe_log('debug', f"Attempt {attempt+1}/{max_retries+1} failed: {err}")

            if attempt < max_retries:
                delay = min(1000 * (2 ** attempt), 30000)
                await sleep(delay)
    
    safe_log('debug', f"All retry attempts failed: {last_error}")
    raise RetryExhaustedError(f"All {max_retries + 1} retry attempts failed. Last error: {last_error}") from last_error


async def send_to_api(
    config: SDKConfig,
    payload: Union[MonitorPayload, ControlPayload], 
    options: dict = {}, 
) -> Union[APIResponse, ControlResponse]:
    """Send payload to API with optional logging."""

    if not config.apiKey:
        safe_log('debug', "API key is not set.")
        raise APIKeyMissingError("[Olakai SDK] API key is not set")
    
    if isinstance(payload, MonitorPayload):
        if config.isBatchingEnabled:
            options = {"priority": options.get("priority", "normal"), "retries": options.get("retries", 0)}
            await add_to_queue(payload, **options)
        else:
            response = await make_api_call(config, [payload], "monitoring")
            # Log any batch-style response information if present
            if (response.totalRequests != None and response.successCount != None):
                safe_log('info', f"Direct API call result: {response.successCount}/{response.totalRequests} requests succeeded")
                if response.failureCount and response.failureCount > 0:
                    safe_log('warning', f"Direct API call result: {response.failureCount}/{response.totalRequests} requests failed")
    
    else:
        return await send_with_retry(config, payload, "control")
