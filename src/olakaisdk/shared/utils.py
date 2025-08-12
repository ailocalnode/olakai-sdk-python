"""
Common utility functions used across the SDK.
"""

import re
import asyncio
import uuid
import traceback
from typing import Any, Dict, Callable, Union, List, Optional
from .logger import safe_log
from .types import JSONType, SanitizePattern

import concurrent.futures
import threading

# Thread-safe executor with proper lifecycle management
_executor = None
_executor_lock = threading.Lock()


def get_executor():
    """Get or create the global executor in a thread-safe way."""
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:
                _executor = concurrent.futures.ThreadPoolExecutor(
                    max_workers=4, thread_name_prefix="olakai-sdk"
                )
    return _executor


def to_json_value(val: Any, sanitize: bool = False, patterns: Optional[List[SanitizePattern]] = None) -> JSONType:
    """
    Convert any value to a JSONType with optional sanitization.
    
    Args:
        val: The value to convert
        sanitize: Whether to sanitize the data using configured patterns
        
    Returns:
        A JSONType value (None, bool, int, float, str, Dict[str, JSONType], List[JSONType])
    """
    try:
        # Handle null and undefined
        if val is None:
            return None
            
        # Handle primitives that are already JSONType
        if isinstance(val, (str, int, float, bool)):
            if sanitize:
                return sanitize_data(str(val), None, patterns)
            return val
            
        # Handle arrays/lists/tuples
        if isinstance(val, (list, tuple)):
            return [to_json_value(item, sanitize, patterns) for item in val]
            
        # Handle dictionaries and objects
        if isinstance(val, dict):
            result = {}
            for key, value in val.items():
                if sanitize:
                    result[str(key)] = sanitize_data(str(value), str(key), patterns)
                else:
                    result[str(key)] = to_json_value(value, sanitize, patterns)
            return result
            
        # Handle objects with __dict__ attribute
        if hasattr(val, '__dict__'):
            obj_dict = val.__dict__
            result = {}
            for key, value in obj_dict.items():
                if sanitize:
                    result[str(key)] = sanitize_data(str(value), str(key), patterns)
                else:
                    result[str(key)] = to_json_value(value, sanitize, patterns)
            return result
            
        # Fallback for other types - convert to string
        return str(val)
        
    except Exception as error:
        safe_log("error", f"Error converting value to JSONType: {error}")
        return str(val)


def sanitize_data(
    data: str, data_key: str, patterns: Optional[List[SanitizePattern]] = None
) -> str:
    """
    Sanitize data by replacing sensitive information with a placeholder.

    Args:
        data: The data to sanitize
        patterns: List of regex patterns to replace
        logger: Optional logger instance

    Returns:
        The sanitized data
    """
    if not patterns:
        return data
    try:
        serialized = data
        for pattern in patterns:
            if pattern.pattern: 
                return re.sub(pattern.pattern, pattern.replacement or "[REDACTED]", serialized)
            elif pattern.key:
                if data_key and pattern.key in data_key:
                    return re.sub(pattern.pattern, pattern.replacement or "[REDACTED]", data)
                else:
                    return data

        safe_log("info", "Data successfully sanitized")
        return serialized
    except Exception as e:
        safe_log("debug", f"Data failed to sanitize: {str(e)}")
        return "[SANITIZED]"



async def create_error_info(error: Exception) -> Dict[str, Any]:
    """
    Create error information dictionary from an exception.

    Args:
        error: The exception to process
        logger: Optional logger instance

    Returns:
        Dictionary containing error message and stack trace
    """
    safe_log("debug", f"Creating error info: {error}")

    return {
        "error_message": str(error),
        "stack_trace": traceback.format_exc()
        if isinstance(error, Exception)
        else None,
    }


async def sleep(ms: int):
    """Sleep for specified milliseconds with logging."""
    safe_log("debug", f"Sleeping for {ms}ms")
    await asyncio.sleep(ms / 1000)


def generate_random_id():
    """Generate a random ID."""
    return str(uuid.uuid4())


def fire_and_forget(func: Callable, *args, **kwargs):
    """Send monitoring without blocking with improved error handling."""

    def send_in_background():
        try:
            if asyncio.iscoroutinefunction(func):
                # For async functions, run in new event loop
                asyncio.run(func(*args, **kwargs))
            else:
                # For sync functions, call directly
                func(*args, **kwargs)
        except Exception as e:
            safe_log("debug", f"Background monitoring failed: {e}")

    executor = get_executor()
    future = executor.submit(send_in_background)

    # Add error callback for better monitoring
    def handle_future_exception(fut):
        try:
            fut.result()
        except Exception as e:
            safe_log("debug", f"Background task failed: {e}")

    future.add_done_callback(handle_future_exception)
    return future
