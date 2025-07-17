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
from .utils import to_api_string
from .logger import get_default_logger, safe_log

# Type variables for generic functions
TArgs = TypeVar('TArgs')
TResult = TypeVar('TResult')

# Global middleware registry
middlewares: List[Middleware] = []

def add_middleware(middleware: Middleware, logger: Optional[logging.Logger] = None) -> None:
    """Add middleware to the global middleware registry."""
    if logger is None:
        logger = get_default_logger()
    middlewares.append(middleware)
    safe_log(logger, 'info', f"Added middleware: {middleware.name}")

def remove_middleware(name: str, logger: Optional[logging.Logger] = None) -> None:
    """Remove middleware from the global middleware registry by name."""
    if logger is None:
        logger = get_default_logger()
    global middlewares
    middlewares = [m for m in middlewares if m.name != name]
    safe_log(logger, 'info', f"Removed middleware: {name}")


def sanitize_data(data: Any, patterns: Optional[List[re.Pattern]] = None, logger: Optional[logging.Logger] = None) -> Any:
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
        logger = get_default_logger()
        
    if not patterns:
        return data
    
    try:
        serialized = json.dumps(data, default=str)
        for pattern in patterns:
            serialized = pattern.sub("[REDACTED]", serialized)
        
        parsed = json.loads(serialized)
        config = get_config()
        if config.verbose:
            safe_log(logger, 'debug', "Data successfully sanitized")
        return parsed
    except Exception:
        config = get_config()
        if config.debug:
            safe_log(logger, 'debug', "Data failed to sanitize")
        return "[SANITIZED]"

def create_error_info(error: Exception, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Create error information dictionary from an exception.
    
    Args:
        error: The exception to process
        
    Returns:
        Dictionary containing error message and stack trace
    """
    if logger is None:
        logger = get_default_logger()
    
    config = get_config()
    if config.debug:
        safe_log(logger, 'debug', f"Creating error info: {error}")
    return {
        "error_message": str(error),
        "stack_trace": traceback.format_exc() if isinstance(error, Exception) else None
    }

def safe_monitoring_operation(operation: Callable[[], Any], context: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Safely execute monitoring operations without affecting the original function.
    
    Args:
        operation: The monitoring operation to execute
        context: Context information for debugging
    """
    if logger is None:
        logger = get_default_logger()
    config = get_config()
        
    try:
        result = operation()
        # Handle async operations
        if asyncio.iscoroutine(result):
            async def handle_async():
                try:
                    await result
                except Exception as error:
                    if config.debug:
                        safe_log(logger, 'debug', f"Monitoring operation failed ({context}): {error}")
                    if config.onError:
                        try:
                            config.onError(error)
                        except Exception as handler_error:
                            if config.debug:
                                safe_log(logger, 'debug', f"Error handler itself failed: {handler_error}")
            
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
            safe_log(logger, 'debug', f"Monitoring operation failed ({context}): {error}")
        if config.onError:
            try:
                config.onError(error)
            except Exception as handler_error:
                if config.debug:
                    safe_log(logger, 'debug', f"Error handler itself failed: {handler_error}")

def monitor(options_or_func: Union[MonitorOptions, Callable, None] = None, options: Optional[MonitorOptions] = None, logger: Optional[logging.Logger] = None):
    """
    Monitor a function with the given options.
    
    Can be used in three ways:
    1. As a decorator without parentheses: @monitor
    2. As a decorator with options: @monitor(options) or @monitor()
    3. As a function wrapper: monitor(func, options)
    
    Args:
        options_or_func: Either MonitorOptions or the function to monitor
        options: MonitorOptions when first argument is a function
        
    Returns:
        The monitored function or decorator
    """
    def create_decorator(monitor_options: MonitorOptions, logger: Optional[logging.Logger] = None):
        if logger is None:
            logger = get_default_logger()
        
        def decorator(func: Callable):
            # Determine if function is async
            is_async = asyncio.iscoroutinefunction(func)
            
            if is_async:
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    return await _monitor_execution(func, monitor_options, args, kwargs, is_async=True, logger=logger)
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    return _monitor_execution(func, monitor_options, args, kwargs, is_async=False, logger=logger)
                return sync_wrapper
        return decorator
    
    # Handle different call patterns
    if options_or_func is None:
        # Called as @monitor() - use default options
        return create_decorator(MonitorOptions(), logger)
    elif isinstance(options_or_func, MonitorOptions):
        # Called as @monitor(options) - use provided options
        return create_decorator(options_or_func, logger)
    elif callable(options_or_func):
        if options is not None:
            # Called as monitor(func, options)
            return create_decorator(options, logger)(options_or_func)
        else:
            # Called as @monitor with no parentheses - use defaults
            return create_decorator(MonitorOptions(), logger)(options_or_func)
    else:
        raise ValueError("Invalid arguments to monitor function")

def _monitor_execution(func: Callable, options: MonitorOptions, args: tuple, kwargs: dict, is_async: bool = False, logger: Optional[logging.Logger] = None):
    """
    Execute the monitored function with monitoring logic.
    
    Args:
        func: The function to execute
        options: Monitor options
        args: Function positional arguments
        kwargs: Function keyword arguments
        is_async: Whether the function is async
        
    Returns:
        The function result
    """
    if logger is None:
        logger = get_default_logger()
        
    # Check if we should monitor this call
    should_monitor_call = False
    try:
        should_monitor_call = True
    except Exception as error:
        safe_monitoring_operation(lambda: None, "shouldMonitor check", logger)
        # If monitoring check fails, still execute the function
        if is_async:
            return asyncio.create_task(func(*args, **kwargs))
        return func(*args, **kwargs)
    
    if not should_monitor_call:
        if is_async:
            return func(*args, **kwargs)
        return func(*args, **kwargs)
    
    # Initialize monitoring data
    config = None
    start = None
    processed_args = args
    
    try:
        config = get_config()
        start = time.time() * 1000  # Convert to milliseconds
    except Exception as error:
        safe_monitoring_operation(lambda: None, "monitoring initialization", logger)
        if is_async:
            return func(*args, **kwargs)
        return func(*args, **kwargs)
    
    # Apply beforeCall middleware
    def apply_before_middleware():
        nonlocal processed_args
        for middleware in middlewares:
            if hasattr(middleware, 'before_call') and middleware.before_call:
                result = middleware.before_call(processed_args)
                if result:
                    processed_args = result
    
    safe_monitoring_operation(apply_before_middleware, "beforeCall middleware", logger)
    
    # Execute the function
    function_error = None
    result = None
    
    try:
        if is_async:
            async def execute_async():
                return await func(*processed_args, **kwargs)
            result = execute_async()
        else:
            result = func(*processed_args, **kwargs)
    except Exception as error:
        function_error = error
        
        # Handle error monitoring
        def handle_error_monitoring(logger: Optional[logging.Logger] = None):
            if logger is None:
                logger = get_default_logger()
                
            # Apply error middleware
            for middleware in middlewares:
                if hasattr(middleware, 'on_error') and middleware.on_error:
                    middleware.on_error(function_error, processed_args)
            
            # Capture error data if onError handler is provided
            if hasattr(options, 'on_error') and options.on_error:
                error_result = options.on_error(function_error, processed_args)
                error_info = create_error_info(function_error, logger)
                
                payload = MonitorPayload(
                    prompt="",
                    response="",
                    errorMessage=to_api_string(error_info["error_message"]) + to_api_string(error_result),
                    chatId="123",
                    userId="anonymous",
                    tokens=None,
                    requestTime=None
                )
                
                send_to_api(payload, {
                    "priority": "high"  # Errors always get high priority
                })
        
        safe_monitoring_operation(handle_error_monitoring, "error monitoring", logger)
        raise error  # Re-raise the original error
    
    # Handle success monitoring
    def handle_success_monitoring(logger: Optional[logging.Logger] = None):
        if logger is None:
            logger = get_default_logger()
            
        nonlocal result
        
        # Apply afterCall middleware
        for middleware in middlewares:
            if hasattr(middleware, 'after_call') and middleware.after_call:
                middleware_result = middleware.after_call(result, processed_args)
                if middleware_result:
                    result = middleware_result
        
        # Capture success data
        if hasattr(options, 'capture') and options.capture:
            capture_result = options.capture({
                "args": processed_args,
                "result": result
            })
            
            # Apply sanitization if enabled
            prompt = capture_result.get("input", "")
            response = capture_result.get("output", "")
            
            if getattr(options, 'sanitize', False):
                sanitize_patterns = getattr(config, 'sanitize_patterns', None)
                prompt = sanitize_data(prompt, sanitize_patterns)
                response = sanitize_data(response, sanitize_patterns)
            
            payload = MonitorPayload(
                prompt=to_api_string(prompt),
                response=to_api_string(response),
                chatId="123",
                userId="anonymous",
                tokens=0,
                requestTime=int(time.time() * 1000 - start),
                errorMessage=None
            )
            
            if config.verbose:
                safe_log(logger, 'info', f"Successfully defined payload: {payload}")
            
            # Send to API
            send_to_api(payload, {
                "priority": getattr(options, 'priority', 'normal')
            })
    
    if function_error is None:
        safe_monitoring_operation(handle_success_monitoring, "success monitoring", logger)
    
    return result
