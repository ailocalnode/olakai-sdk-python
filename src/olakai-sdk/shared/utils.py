"""
Common utility functions used across the SDK.
"""
import json
import traceback
import asyncio
from typing import Any, Callable, Optional, Dict
import logging
from .logger import get_default_logger, safe_log


async def to_string_api(data: Any) -> str:
    """Convert data to API string format with enhanced handling."""
    if data is None or data == "" or data == "None" or data == "null" or data == "Null":
        return "Empty data"

    if isinstance(data, str):
        return data
    
    if isinstance(data, (tuple, list)):
        returned = ""
        for item in data:
            try:
                item = await to_string_api(item)
                returned += item
            except Exception:
                item = str(item)
                returned += item
        return returned
    
    try:
        return json.dumps(data, default=str)
    except Exception:
        return str(data)


async def execute_func(f: Callable, *args, **kwargs) -> Any:
    """Execute a function with arguments, handling both sync and async functions."""
    if "potential_result" in kwargs:
        return kwargs["potential_result"]
    
    try:
        if asyncio.iscoroutinefunction(f):
            return await f(*args, **kwargs)
        else:
            return f(*args, **kwargs)
    except Exception as e:
        raise e


async def create_error_info(error: Exception, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Create error information dictionary from an exception.
    
    Args:
        error: The exception to process
        logger: Optional logger instance
        
    Returns:
        Dictionary containing error message and stack trace
    """
    if logger is None:
        logger = get_default_logger()
    
    safe_log(logger, 'debug', f"Creating error info: {error}")
    
    return {
        "error_message": str(error),
        "stack_trace": traceback.format_exc() if isinstance(error, Exception) else None
    } 