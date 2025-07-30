"""
Common utility functions used across the SDK.
"""
import json
import asyncio
import uuid
import time
import traceback
from typing import Any, Dict, Callable, Literal
from .logger import safe_log


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
    time.sleep(ms / 1000)

def generate_random_id():
    """Generate a random ID."""
    return str(uuid.uuid4())

def run_async_in_sync( thread: Literal["parallel", "sequential"], func: Callable, *args, **kwargs) -> Any:
    """Run an async function in a synchronous context."""
    if thread == "parallel":
        try:
            loop = asyncio.get_running_loop()
            # If there's a running loop, we need to run should_block in a separate thread
            # to avoid blocking the current thread
            import concurrent.futures
                    
            def run_func():
                return asyncio.run(func(*args, **kwargs))
                    
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_func)
                return future.result()
        except RuntimeError:
            # No running loop, create a new one
            return asyncio.run(func(*args, **kwargs))
        except Exception as e:
            safe_log('error', f"Error running async function in sync: {e}")
            raise e
    elif thread == "sequential":
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop).result()
            else:
                return asyncio.run(func(*args, **kwargs))

        except Exception as e:
            safe_log('error', f"Error running async function in sync: {e}")
            raise e
    