import asyncio
import json
import time
import logging
from typing import Any, Callable, List, Optional, TypeVar
import re

from .client import send_to_api, get_config
from .types import MonitorOptions, Middleware, MonitorPayload
from .utils import to_api_string, execute_func, toStringApi, create_error_info
from .logger import get_default_logger, safe_log

# Type variables for generic functions
TArgs = TypeVar('TArgs')
TResult = TypeVar('TResult')

# Global middleware registry
middlewares: List[Middleware] = []

async def add_middleware(middleware: Middleware, logger: Optional[logging.Logger] = None) -> None:
    """Add middleware to the global middleware registry."""
    if logger is None:
        logger =await get_default_logger()
    middlewares.append(middleware)
    c = safe_log(logger, 'info', f"Added middleware: {middleware.name}")

async def remove_middleware(name: str, logger: Optional[logging.Logger] = None) -> None:
    """Remove middleware from the global middleware registry by name."""
    if logger is None:
        logger = await get_default_logger()
    global middlewares
    middlewares = [m for m in middlewares if m.name != name]
    c = safe_log(logger, 'info', f"Removed middleware: {name}")


async def sanitize_data(data: Any, patterns: Optional[List[re.Pattern]] = None, logger: Optional[logging.Logger] = None) -> Any:
    """
    Sanitize data by replacing sensitive information with a placeholder.
    
    Args:
        data: The data to sanitize
        patterns: List of regex patterns to replace
        logger: Optional logger instance
        
    Returns:
        The sanitized data
    """
    if logger is None:
        logger = await get_default_logger()
        
    if not patterns:
        return data
    config = await get_config()
    try:
        serialized = json.dumps(data, default=str)
        for pattern in patterns:
            serialized = pattern.sub("[REDACTED]", serialized)
        
        parsed = json.loads(serialized)

        if config.verbose:
            c = safe_log(logger, 'debug', "Data successfully sanitized")
        return parsed
    except Exception:
        if config.debug:
            c = safe_log(logger, 'debug', "Data failed to sanitize")
        return "[SANITIZED]"


def monitor(options: MonitorOptions, logger: logging.Logger):
    """
    Monitor a function with the given options.
    
    Args:
        options: Monitor options
        logger: Optional logger instance
    """
    def wrap(f: Callable) -> Callable:
        async def async_wrapped_f(*args, **kwargs):
            await safe_log(logger, 'debug', f"Monitoring function: {f.__name__}")
            await safe_log(logger, 'debug', f"Arguments: {args}")

            try:
                config = await get_config()
                start = time.time() * 1000  # Convert to milliseconds
                processed_args = args
                
                # Apply before middleware
                for middleware in middlewares:
                    if hasattr(middleware, 'before_call') and middleware.before_call:
                        try:
                            middleware_result = middleware.before_call(processed_args)
                            if middleware_result:
                                processed_args = middleware_result
                        except Exception as middleware_error:
                            await safe_log(logger, 'debug', f"Middleware error: {middleware_error}")
                await safe_log(logger, 'debug', f"Processed arguments: {processed_args}")

                # Execute the function
                function_error = None
                result = None
                        
                try:
                    result = await execute_func(f, *processed_args, **kwargs)
                    await safe_log(logger, 'debug', f"Function executed successfully")
                except Exception as error:
                    function_error = error
                    await safe_log(logger, 'debug', f"Function execution failed: {error}")
                            
                    # Handle error monitoring
                    async def handle_error_monitoring():
                        # Apply error middleware
                        for middleware in middlewares:
                            if hasattr(middleware, 'on_error') and middleware.on_error:
                                try:
                                    middleware.on_error(function_error, processed_args)
                                except Exception as middleware_error:
                                    await safe_log(logger, 'debug', f"Error middleware failed: {middleware_error}")
                                
                        # Capture error data if onError handler is provided
                        if hasattr(options, 'on_error') and options.on_error:
                            try:
                                error_result = options.on_error(function_error, processed_args)
                                error_info = await create_error_info(function_error, logger)
                                        
                                payload = MonitorPayload(
                                    prompt="",
                                    response="",
                                    errorMessage=to_api_string(error_info["error_message"]) + to_api_string(error_result),
                                    chatId="123",
                                    email="anonymous@olakai.ai",
                                    shouldScore=getattr(options, 'shouldScore', False),
                                    tokens=0,
                                    requestTime=int(time.time() * 1000 - start),
                                    task=getattr(options, 'task', None),
                                    subTask=getattr(options, 'subTask', None)
                                )
                                        
                                await send_to_api(payload, {
                                    "priority": "high"  # Errors always get high priority
                                })
                            except Exception as capture_error:
                                await safe_log(logger, 'debug', f"Error capture failed: {capture_error}")

                    try:
                        await handle_error_monitoring()
                    except Exception as error:
                        await safe_log(logger, 'debug', f"Error handling error monitoring: {error}")
                    raise function_error  # Re-raise the original error
                        
                # Handle success monitoring
                async def handle_success_monitoring():
                    nonlocal result
                            
                    # Apply afterCall middleware
                    for middleware in middlewares:
                        if hasattr(middleware, 'after_call') and middleware.after_call:
                            try:
                                middleware_result = middleware.after_call(result, processed_args)
                                if middleware_result:
                                    result = middleware_result
                            except Exception as middleware_error:
                                await safe_log(logger, 'debug', f"After middleware failed: {middleware_error}")

                    await safe_log(logger, 'info', f"Result: {result}")
                    # Capture success data
                    if hasattr(options, 'capture') and options.capture:
                        capture_result = options.capture(
                            args=processed_args,
                            result=result
                        )
                                    
                        # Apply sanitization if enabled
                        prompt = capture_result.get("input", "")
                        response = capture_result.get("output", "")

                        await safe_log(logger, 'info', f"Prompt: {prompt}")
                        await safe_log(logger, 'info', f"Response: {response}")

                        if getattr(options, 'sanitize', False):
                            sanitize_patterns = getattr(config, 'sanitize_patterns', None)
                            prompt = await sanitize_data(prompt, sanitize_patterns, logger)
                            response = await sanitize_data(response, sanitize_patterns, logger)

                        await safe_log(logger, 'info', f"Sanitized prompt: {prompt}")
                        # Handle chatId and userId
                        chatId = "anonymous"
                        email = "anonymous@olakai.ai"
                        
                        if hasattr(options, 'chatId'):
                            if callable(options.chatId):
                                try:
                                    chatId = options.chatId()
                                    if not isinstance(chatId, str):
                                        chatId = str(chatId)
                                except Exception:
                                    chatId = "anonymous"
                                    await safe_log(logger, 'debug', f"Error getting chatId")
                            else:
                                chatId = options.chatId
                                
                        if hasattr(options, 'email'):
                            if callable(options.email):
                                try:
                                    email = options.email()
                                    if not isinstance(email, str):
                                        email = str(email)
                                except Exception:
                                    email = "anonymous@olakai.ai"
                                    await safe_log(logger, 'debug', f"Error getting email")
                            else:
                                email = options.email

                        payload = MonitorPayload(
                            prompt=await toStringApi(prompt),
                            response=await toStringApi(response),
                            chatId=chatId if chatId else "anonymous",
                            email=email if email else "anonymous@olakai.ai",
                            shouldScore=getattr(options, 'shouldScore', False),
                            tokens=0,
                            requestTime=int(time.time() * 1000 - start),
                            errorMessage=None,
                            task=getattr(options, 'task', None),
                            subTask=getattr(options, 'subTask', None)
                        )

                        await safe_log(logger, 'info', f"Successfully defined payload: {payload}")
                                    
                        # Send to API (this is the async API call you want!)
                        await send_to_api(payload, {
                            "priority": getattr(options, 'priority', 'normal')
                        }, logger)
                        
                if function_error is None:
                    try:
                        await handle_success_monitoring()
                    except Exception as error:
                        await safe_log(logger, 'debug', f"Error handling success monitoring: {error}")
                return result
                
            except Exception as error:
                await safe_log(logger, 'error', f"Error: {error}")
                if (function_error is not None):
                    raise function_error
                result = await execute_func(f, *args, **kwargs)
                return result
        
        # Check if the decorated function is async or sync
        if asyncio.iscoroutinefunction(f):
            # For async functions, return the async wrapper directly
            return async_wrapped_f
        else:
            # For sync functions, create a sync wrapper that fires off monitoring in background
            def sync_wrapped_f(*args, **kwargs):
                
                try:
                    result = f(*args, **kwargs)
                except Exception as error:
                    raise error
                
                # Fire off async monitoring in background (don't wait for it)
                def fire_and_forget_monitoring():
                    try:
                        # Check if there's already an event loop running
                        try:
                            loop = asyncio.get_running_loop()
                            # If there's a running loop, schedule the monitoring as a task
                            asyncio.create_task(async_wrapped_f(*args, **kwargs, potential_result=result))
                        except RuntimeError:
                            # No running loop, create a new one for monitoring
                            # Run in a separate thread to avoid blocking the sync function
                            import threading
                            def run_monitoring():
                                asyncio.run(async_wrapped_f(*args, **kwargs, potential_result=result))
                            
                            thread = threading.Thread(target=run_monitoring, daemon=True)
                            thread.start()
                    except Exception:
                        # If monitoring fails, don't affect the original function
                        pass
                
                # Start background monitoring
                fire_and_forget_monitoring()
                
                # Return the original result or raise the original error
                return result
            
            return sync_wrapped_f
    
    return wrap
