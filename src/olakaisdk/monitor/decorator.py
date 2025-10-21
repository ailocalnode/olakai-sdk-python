"""
Simplified monitoring decorator functionality.
"""

import asyncio
import time
from dataclasses import asdict
from typing import Any, Callable
from ..shared import (
    MonitorOptions,
    MonitorPayload,
    OlakaiConfig,
)
from ..client import send_to_api_simple
from ..core import get_config


def olakai_monitor(**kwargs):
    """
    Monitor a function with the given options (simplified version).

    Kwargs:
        userEmail: str
        chatId: str
        task: str
        subTask: str
        customDimensions: Dict[str, str]
        customMetrics: Dict[str, float]
        shouldScore: bool

    Returns:
        Decorator function
    """
    options = MonitorOptions()
    if len(kwargs) > 0:
        for key, value in kwargs.items():
            if hasattr(options, key):
                try:
                    setattr(options, key, value)
                except Exception as e:
                    print(f"Error setting attribute, check the type of the value: {e}")
            else:
                print(f"Invalid keyword argument: {key}")

    def wrap(f: Callable) -> Callable:
        async def async_wrapped_f(*args, **kwargs):
            try:
                # Execute the function
                result = await f(*args, **kwargs)

                # Create monitoring payload
                payload = MonitorPayload(
                    prompt=str(args) + str(kwargs),
                    response=str(result),
                    userEmail=options.userEmail or "anonymous@olakai.ai",
                    chatId=options.chatId or "anonymous",
                    tokens=0,
                    requestTime=0,  # Simplified - no timing
                    task=options.task,
                    subTask=options.subTask,
                    customDimensions=options.customDimensions,
                    customMetrics=options.customMetrics,
                    shouldScore=options.shouldScore,
                )

                # Send to API
                config = get_config()
                if config:
                    await send_to_api_simple(config, payload)

                return result

            except Exception as error:
                # Create error payload
                payload = MonitorPayload(
                    prompt=str(args) + str(kwargs),
                    response=f"Error: {str(error)}",
                    userEmail=options.userEmail or "anonymous@olakai.ai",
                    chatId=options.chatId or "anonymous",
                    tokens=0,
                    requestTime=0,  # Simplified - no timing
                    task=options.task,
                    subTask=options.subTask,
                    customDimensions=options.customDimensions,
                    customMetrics=options.customMetrics,
                    shouldScore=options.shouldScore,
                )

                # Send error to API
                config = get_config()
                if config:
                    await send_to_api_simple(config, payload)
                
                raise error  # Re-raise the original error

        def sync_wrapped_f(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                
                # Create monitoring payload
                payload = MonitorPayload(
                    prompt=str(args) + str(kwargs),
                    response=str(result),
                    userEmail=options.userEmail or "anonymous@olakai.ai",
                    chatId=options.chatId or "anonymous",
                    tokens=0,
                    requestTime=0,  # Simplified - no timing
                    task=options.task,
                    subTask=options.subTask,
                    customDimensions=options.customDimensions,
                    customMetrics=options.customMetrics,
                    shouldScore=options.shouldScore,
                )

                # Send to API asynchronously
                config = get_config()
                if config:
                    asyncio.create_task(send_to_api_simple(config, payload))
                
                return result
                
            except Exception as error:
                # Create error payload
                payload = MonitorPayload(
                    prompt=str(args) + str(kwargs),
                    response=f"Error: {str(error)}",
                    userEmail=options.userEmail or "anonymous@olakai.ai",
                    chatId=options.chatId or "anonymous",
                    tokens=0,
                    requestTime=0,  # Simplified - no timing
                    task=options.task,
                    subTask=options.subTask,
                    customDimensions=options.customDimensions,
                    customMetrics=options.customMetrics,
                    shouldScore=options.shouldScore,
                )

                # Send error to API asynchronously
                config = get_config()
                if config:
                    asyncio.create_task(send_to_api_simple(config, payload))
                
                raise error

        # Check if the decorated function is async or sync
        if asyncio.iscoroutinefunction(f):
            # For async functions, return the async wrapper directly
            return async_wrapped_f
        else:
            # For sync functions, create a sync wrapper that fires off monitoring in background
            return sync_wrapped_f

    return wrap


# Legacy function for backward compatibility
def olakai_supervisor(**kwargs):
    """
    Legacy function name for backward compatibility.
    Use olakai_monitor instead.
    """
    return olakai_monitor(**kwargs)
