import json
import traceback
from typing import Any, Callable, Optional, Dict, Union
import asyncio
from .types import MonitorOptions
from dataclasses import dataclass
from .logger import get_default_logger, safe_log
from .monitor import monitor
from .types import MonitorOptions
import logging

def to_api_string(data: Any) -> str:
    """Convert data to API string format."""
    if isinstance(data, str):
        return data
    try:
        return json.dumps(data, default=str)
    except Exception:
        return str(data)

async def execute_func(f:Callable, *args, **kwargs) -> None:
    """Execute a function with arguments and return None."""
    if "potential_result" in kwargs:
        return kwargs["potential_result"]
    try:
        if asyncio.iscoroutinefunction(f):
            return await f(*args, **kwargs)
        else:
            return f(*args, **kwargs)
    except Exception as e:
        raise e

@dataclass
class MonitorUtils:
    def capture_all_f(**kwargs):
        return {
            "input": kwargs["args"],
            "output": kwargs["result"]
        }
    capture_all = MonitorOptions(capture=capture_all_f)
    
    def capture_input_f(**kwargs):
        return {
            "input": kwargs["args"],
            "output": "Function executed successfully"
        }
    capture_input = MonitorOptions(capture=capture_input_f)

    def capture_output_f(**kwargs):
        return {
            "input": "Function called",
            "output": kwargs["result"]
        }
    capture_output = MonitorOptions(capture=capture_output_f)


def olakai_monitor(options: Optional[Union[Dict[str, Any], MonitorOptions]] = None, logger: Optional[logging.Logger] = None):
    if options is None:
        options = MonitorUtils.capture_all
    elif isinstance(options, MonitorOptions):
        pass
    else:
        # If it's a dictionary, create MonitorOptions from it
        for key, _ in options.items():
            if key not in MonitorOptions.__dataclass_fields__:
                safe_log(logger, 'debug', f"Invalid option: {key}")
                del options[key]
        if "capture" not in options:
            options["capture"] = MonitorUtils.capture_all_f
        options = MonitorOptions(**options)

    return monitor(options, logger)


async def toStringApi(data: Any) -> str:
    """Convert data to API string format."""
    if data is None or data == "" or data == "None" or data == "null" or data == "Null":
        return "Empty data"

    if isinstance(data, str):
        return data
    if isinstance(data, tuple):
        returned = ""
        for item in data:
            try:
                item = await toStringApi(item)
                returned += item
            except Exception:
                item = str(item)
                returned += item
        return returned
    if isinstance(data, list):
        returned = ""
        for item in data:
            try:
                item = await toStringApi(item)
                returned += item
            except Exception:
                item = str(item)
                returned += item
        return returned
    try:
        return json.dumps(data, default=str)
    except Exception:
        return str(data)


async def create_error_info(error: Exception, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Create error information dictionary from an exception.
    
    Args:
        error: The exception to process
        
    Returns:
        Dictionary containing error message and stack trace
    """
    if logger is None:
        logger = await get_default_logger()
    
    await safe_log(logger, 'debug', f"Creating error info: {error}")
    
    return {
        "error_message": str(error),
        "stack_trace": traceback.format_exc() if isinstance(error, Exception) else None
    }