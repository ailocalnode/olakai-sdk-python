"""
Common utility functions used across the SDK.
"""
import json
import asyncio
import uuid
import traceback
from typing import Any, Dict, Callable
from .logger import safe_log

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
                    max_workers=4, 
                    thread_name_prefix="olakai-sdk"
                )
    return _executor


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

async def create_error_info(error: Exception) -> Dict[str, Any]:
    """
    Create error information dictionary from an exception.
    
    Args:
        error: The exception to process
        logger: Optional logger instance
        
    Returns:
        Dictionary containing error message and stack trace
    """
    safe_log('debug', f"Creating error info: {error}")
    
    return {
        "error_message": str(error),
        "stack_trace": traceback.format_exc() if isinstance(error, Exception) else None
    } 


async def sleep(ms: int):
    """Sleep for specified milliseconds with logging."""
    safe_log('debug', f"Sleeping for {ms}ms")
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
            safe_log('debug', f"Background monitoring failed: {e}")
    
    executor = get_executor()
    future = executor.submit(send_in_background)
    # Add error callback for better monitoring
    def handle_future_exception(fut):
        try:
            fut.result()
        except Exception as e:
            safe_log('debug', f"Background task failed: {e}")
    
    future.add_done_callback(handle_future_exception)
    return future
    