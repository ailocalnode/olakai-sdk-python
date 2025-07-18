import asyncio
import json
import time
import traceback
import logging
from dataclasses import asdict
from typing import Any, Callable, List, Optional, Union, TypeVar, Generic, Dict, Awaitable
from functools import wraps
import re

from .client import send_to_api, get_config
from .types import MonitorOptions, Middleware, MonitorPayload
from .utils import to_api_string, execute_func
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
    
    config = await get_config()
    if config.debug:
        c = safe_log(logger, 'debug', f"Creating error info: {error}")
    return {
        "error_message": str(error),
        "stack_trace": traceback.format_exc() if isinstance(error, Exception) else None
    }

async def safe_monitoring_operation(operation: Callable[[], Any], context: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Safely execute monitoring operations without affecting the original function.
    
    Args:
        operation: The monitoring operation to execute
        context: Context information for debugging
    """
    if logger is None:
        logger = await get_default_logger()
    config = await get_config()
        
    try:
        result = operation()
        # Handle async operations
        if asyncio.iscoroutine(result):
            async def handle_async():
                try:
                    await result
                except Exception as error:
                    if config.debug:
                        c = safe_log(logger, 'debug', f"Monitoring operation failed ({context}): {error}")
                    if config.onError:
                        try:
                            config.onError(error)
                        except Exception as handler_error:
                            if config.debug:
                                c = safe_log(logger, 'debug', f"Error handler itself failed: {handler_error}")
            
            # Schedule the async operation
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(handle_async())
                else:
                    loop.run_until_complete(handle_async())
            except RuntimeError:
                # No event loop running
                asyncio.run(handle_async())
                
    except Exception as error:
        if config.debug:
            c = safe_log(logger, 'debug', f"Monitoring operation failed ({context}): {error}")
        if config.onError:
            try:
                config.onError(error)
            except Exception as handler_error:
                if config.debug:
                    c = safe_log(logger, 'debug', f"Error handler itself failed: {handler_error}")


def olakai_monitor(options: MonitorOptions, logger: logging.Logger):
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

                # Execute the function
                function_error = None
                result = None
                        
                try:
                    result = await execute_func(f, *processed_args, **kwargs)
                except Exception as error:
                    function_error = error
                            
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
                                    userId="anonymous",
                                    tokens=0,
                                    requestTime=int(time.time() * 1000 - start)
                                )
                                        
                                await send_to_api(payload, {
                                    "priority": "high"  # Errors always get high priority
                                })
                            except Exception as capture_error:
                                await safe_log(logger, 'debug', f"Error capture failed: {capture_error}")
                            
                    await safe_monitoring_operation(handle_error_monitoring, "error monitoring", logger)
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
                            
                    # Capture success data
                    if hasattr(options, 'capture') and options.capture:
                        capture_result = options.capture(
                            args=processed_args,
                            result=result
                        )
                                    
                        # Apply sanitization if enabled
                        prompt = capture_result.get("input", "")
                        response = capture_result.get("output", "")
                                    
                        if getattr(options, 'sanitize', False):
                            sanitize_patterns = getattr(config, 'sanitize_patterns', None)
                            prompt = await sanitize_data(prompt, sanitize_patterns, logger)
                            response = await sanitize_data(response, sanitize_patterns, logger)

                        # Handle chatId and userId
                        chatId = "anonymous"
                        userId = "anonymous"
                        
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
                                
                        if hasattr(options, 'userId'):
                            if callable(options.userId):
                                try:
                                    userId = options.userId()
                                    if not isinstance(userId, str):
                                        userId = str(userId)
                                except Exception:
                                    userId = "anonymous"
                                    await safe_log(logger, 'debug', f"Error getting userId")
                            else:
                                userId = options.userId

                        payload = MonitorPayload(
                            prompt=to_api_string(prompt),
                            response=to_api_string(response),
                            chatId=chatId if chatId else "anonymous",
                            userId=userId if userId else "anonymous",
                            tokens=0,
                            requestTime=int(time.time() * 1000 - start),
                            errorMessage=None
                        )

                        await safe_log(logger, 'info', f"Successfully defined payload: {payload}")
                                    
                        # Send to API
                        await send_to_api(payload, {
                            "priority": getattr(options, 'priority', 'normal')
                        })
                        
                if function_error is None:
                    await safe_monitoring_operation(handle_success_monitoring, "success monitoring", logger)
                return result
                
            except Exception as error:
                await safe_monitoring_operation(lambda: None, "monitoring initialization", logger)
                await safe_log(logger, 'error', f"Error: {error}")
                result = await execute_func(f, *args, **kwargs)
                return result
                
        return async_wrapped_f
    return wrap
