"""
Simplified API communication module for the Olakai SDK.
"""

from dataclasses import asdict
from typing import Union, Literal
import asyncio
from ..shared import (
    APITimeoutError,
    APIResponseError,
    RetryExhaustedError,
    MonitorPayload,
    ControlPayload,
    OlakaiConfig,
    APIResponse,
    ControlResponse,
    ControlDetails,
)

# Import requests only when needed
try:
    import requests
except ImportError:
    requests = None


async def make_api_call(
    config: OlakaiConfig,
    payload: Union[MonitorPayload, ControlPayload],
    call_type: Literal["monitoring", "control"] = "monitoring",
) -> Union[APIResponse, ControlResponse]:
    """Make API call with optional logging."""

    if requests is None:
        raise ImportError("requests library is required for API calls. Install with: pip install requests")

    headers = {"x-api-key": config.api_key}
    data_dict = asdict(payload)

    # Clean up None values
    if call_type == "monitoring":
        if "errorMessage" in data_dict and data_dict["errorMessage"] is None:
            del data_dict["errorMessage"]
        if "task" in data_dict and data_dict["task"] is None:
            del data_dict["task"]
        if "subTask" in data_dict and data_dict["subTask"] is None:
            del data_dict["subTask"]
        if "customDimensions" in data_dict and data_dict["customDimensions"] is None:
            del data_dict["customDimensions"]
        if "customMetrics" in data_dict and data_dict["customMetrics"] is None:
            del data_dict["customMetrics"]
        if "shouldScore" in data_dict and data_dict["shouldScore"] is None:
            del data_dict["shouldScore"]
    else:
        if "overrideControlCriteria" in data_dict and data_dict["overrideControlCriteria"] is None:
            del data_dict["overrideControlCriteria"]
        if "task" in data_dict and data_dict["task"] is None:
            del data_dict["task"]
        if "subTask" in data_dict and data_dict["subTask"] is None:
            del data_dict["subTask"]

    try:
        # Determine URL based on call type
        if call_type == "monitoring":
            url = f"{config.endpoint}/api/monitoring/prompt"
        else:
            url = f"{config.endpoint}/api/control/prompt"

        response = requests.post(
            url,
            json=data_dict,
            headers=headers,
            timeout=30,  # Fixed timeout
        )
        
        if config.debug:
            print(f"API call to {url}: {response.status_code}")
        
        response.raise_for_status()
        result = response.json()

        if call_type == "monitoring":
            return APIResponse(**result)
        else:
            result["details"] = ControlDetails(**result["details"])
            return ControlResponse(**result)

    except requests.exceptions.Timeout as err:
        raise APITimeoutError(f"Request timed out after 30 seconds") from err
    except requests.exceptions.HTTPError as err:
        raise APIResponseError(
            f"HTTP error: {err.response.status_code} - {err.response.text}"
        ) from err
    except requests.exceptions.RequestException as err:
        raise APIResponseError(f"Request failed: {str(err)}") from err
    except Exception as err:
        raise APIResponseError(f"Unexpected error during API call: {str(err)}") from err


async def send_with_retry(
    config: OlakaiConfig,
    payload: Union[MonitorPayload, ControlPayload],
    call_type: Literal["monitoring", "control"] = "monitoring",
    max_retries: int = 3,
) -> Union[APIResponse, ControlResponse]:
    """Send payload with retry logic."""

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            result = await make_api_call(config, payload, call_type)
            if config.debug:
                print("API call successful")
            return result
        except (APITimeoutError, APIResponseError) as err:
            last_error = err

            if config.debug:
                print(f"Attempt {attempt + 1}/{max_retries + 1} failed: {err}")

            if attempt < max_retries:
                delay = min(1000 * (2**attempt), 30000)  # Exponential backoff
                await asyncio.sleep(delay / 1000)  # Convert to seconds

    if config.debug:
        print(f"All retry attempts failed: {last_error}")
    raise RetryExhaustedError(
        f"All {max_retries + 1} retry attempts failed. Last error: {last_error}"
    ) from last_error


async def send_to_api_simple(
    config: OlakaiConfig,
    payload: MonitorPayload,
) -> Union[APIResponse, ControlResponse]:
    """Send payload to API with simplified logic."""
    try:
        return await send_with_retry(config, payload, "monitoring")
    except Exception as e:
        if config.debug:
            print(f"Error sending payload to API: {e}")
        raise e


# Legacy function for backward compatibility
async def send_to_api(
    config: OlakaiConfig,
    payload: Union[MonitorPayload, ControlPayload],
    options: dict = {},
) -> Union[APIResponse, ControlResponse]:
    """Send payload to API (legacy function for backward compatibility)."""
    if isinstance(payload, MonitorPayload):
        return await send_to_api_simple(config, payload)
    else:
        return await send_with_retry(config, payload, "control")