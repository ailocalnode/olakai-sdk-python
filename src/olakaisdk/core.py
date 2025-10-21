"""
Core simplified API for the Olakai SDK.
"""

import time
import asyncio
from typing import Callable, Optional, Dict, Any
from .shared.types import OlakaiConfig, OlakaiEventParams, MonitorPayload
from .shared.exceptions import APIKeyMissingError, InitializationError
from .client.api import send_to_api_simple

# Global configuration
_global_config: Optional[OlakaiConfig] = None


def olakai_config(api_key: str, endpoint: str = "https://app.olakai.ai", debug: bool = False) -> None:
    """
    Initialize the Olakai SDK with simplified configuration.
    
    Args:
        api_key: Your Olakai API key
        endpoint: API endpoint URL (default: https://app.olakai.ai)
        debug: Enable debug logging (default: False)
    """
    global _global_config
    
    if not api_key:
        raise APIKeyMissingError("API key is required to initialize the Olakai SDK.")
    
    _global_config = OlakaiConfig(
        api_key=api_key,
        endpoint=endpoint,
        debug=debug
    )
    
    if debug:
        print(f"Olakai SDK initialized with endpoint: {endpoint}")


def olakai(event_type: str, event_name: str, params: OlakaiEventParams) -> None:
    """
    Track an event with the Olakai API.
    
    Args:
        event_type: Type of event (e.g., "ai_activity")
        event_name: Name of the event
        params: Event parameters
    """
    if _global_config is None:
        raise InitializationError("Olakai SDK not initialized. Call olakai_config() first.")
    
    # Convert to MonitorPayload for API compatibility
    payload = MonitorPayload(
        userEmail=params.userEmail or "anonymous@olakai.ai",
        chatId=params.chatId or "anonymous",
        prompt=params.prompt,
        response=params.response,
        tokens=params.tokens,
        requestTime=params.requestTime,
        task=params.task,
        subTask=params.subTask,
        customDimensions=params.customDimensions,
        customMetrics=params.customMetrics,
        shouldScore=params.shouldScore
    )
    
    # Send asynchronously in background if possible, otherwise ignore
    try:
        loop = asyncio.get_running_loop()
        asyncio.create_task(send_to_api_simple(_global_config, payload))
    except RuntimeError:
        # No event loop running, skip API call
        if _global_config.debug:
            print(f"Skipping API call - no event loop running")


def olakai_report(prompt: str, response: str, options: Dict[str, Any] = None) -> None:
    """
    Direct reporting function for simple event tracking.
    
    Args:
        prompt: The input prompt
        response: The response
        options: Optional parameters (email, chatId, task, subTask, etc.)
    """
    if options is None:
        options = {}
    
    params = OlakaiEventParams(
        prompt=prompt,
        response=response,
        userEmail=options.get("userEmail", "anonymous@olakai.ai"),
        chatId=options.get("chatId"),
        task=options.get("task"),
        subTask=options.get("subTask"),
        customDimensions=options.get("customDimensions"),
        customMetrics=options.get("customMetrics"),
        shouldScore=options.get("shouldScore", True),
        tokens=options.get("tokens", 0),
        requestTime=options.get("requestTime", 0)
    )
    
    olakai("ai_activity", "direct_report", params)


def olakai_monitor(fn: Callable = None, **options):
    """
    Decorator for automatic function monitoring.
    
    Args:
        fn: Function to monitor (when used as decorator)
        **options: Monitoring options (email, chatId, task, subTask, etc.)
    """
    def decorator(func: Callable) -> Callable:
        def sync_wrapper(*args, **kwargs):
            start_time = time.time() * 1000
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Create event parameters
                params = OlakaiEventParams(
                    prompt=str(args) + str(kwargs),
                    response=str(result),
                    userEmail=options.get("userEmail", "anonymous@olakai.ai"),
                    chatId=options.get("chatId"),
                    task=options.get("task"),
                    subTask=options.get("subTask"),
                    customDimensions=options.get("customDimensions"),
                    customMetrics=options.get("customMetrics"),
                    shouldScore=options.get("shouldScore", True),
                    tokens=0,
                    requestTime=int(time.time() * 1000 - start_time)
                )
                
                # Track the event
                olakai("ai_activity", func.__name__, params)
                
                return result
                
            except Exception as e:
                # Track error event
                params = OlakaiEventParams(
                    prompt=str(args) + str(kwargs),
                    response=f"Error: {str(e)}",
                    userEmail=options.get("userEmail", "anonymous@olakai.ai"),
                    chatId=options.get("chatId"),
                    task=options.get("task"),
                    subTask=options.get("subTask"),
                    customDimensions=options.get("customDimensions"),
                    customMetrics=options.get("customMetrics"),
                    shouldScore=options.get("shouldScore", True),
                    tokens=0,
                    requestTime=int(time.time() * 1000 - start_time)
                )
                
                olakai("ai_activity", f"{func.__name__}_error", params)
                raise
        
        async def async_wrapper(*args, **kwargs):
            start_time = time.time() * 1000
            
            try:
                # Execute the async function
                result = await func(*args, **kwargs)
                
                # Create event parameters
                params = OlakaiEventParams(
                    prompt=str(args) + str(kwargs),
                    response=str(result),
                    userEmail=options.get("userEmail", "anonymous@olakai.ai"),
                    chatId=options.get("chatId"),
                    task=options.get("task"),
                    subTask=options.get("subTask"),
                    customDimensions=options.get("customDimensions"),
                    customMetrics=options.get("customMetrics"),
                    shouldScore=options.get("shouldScore", True),
                    tokens=0,
                    requestTime=int(time.time() * 1000 - start_time)
                )
                
                # Track the event
                olakai("ai_activity", func.__name__, params)
                
                return result
                
            except Exception as e:
                # Track error event
                params = OlakaiEventParams(
                    prompt=str(args) + str(kwargs),
                    response=f"Error: {str(e)}",
                    userEmail=options.get("userEmail", "anonymous@olakai.ai"),
                    chatId=options.get("chatId"),
                    task=options.get("task"),
                    subTask=options.get("subTask"),
                    customDimensions=options.get("customDimensions"),
                    customMetrics=options.get("customMetrics"),
                    shouldScore=options.get("shouldScore", True),
                    tokens=0,
                    requestTime=int(time.time() * 1000 - start_time)
                )
                
                olakai("ai_activity", f"{func.__name__}_error", params)
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    # Handle both @olakai_monitor and @olakai_monitor(options) usage
    if fn is None:
        return decorator
    else:
        return decorator(fn)


def get_config() -> Optional[OlakaiConfig]:
    """Get the current SDK configuration."""
    return _global_config
