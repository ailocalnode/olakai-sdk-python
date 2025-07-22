"""
Core monitoring decorator functionality.
"""
import asyncio
import time
import logging
import threading
from typing import Any, Callable, Optional
from .types import MonitorOptions
from .middleware import get_middlewares
from .processor import process_capture_result, extract_user_info
from ..client.types import MonitorPayload
from ..client.api import send_to_api
from ..shared.utils import execute_func, create_error_info, to_string_api
from ..shared.logger import get_default_logger, safe_log


def monitor(options: Optional[MonitorOptions] = None, logger: Optional[logging.Logger] = None):
    """
    Monitor a function with the given options.
    
    Args:
        options: Monitor options
        logger: Optional logger instance
        
    Returns:
        Decorator function
    """
    if options is None:
        options = MonitorOptions()
    
    def wrap(f: Callable) -> Callable:
        async def async_wrapped_f(*args, **kwargs):
            if logger is None:
                current_logger = get_default_logger()
            else:
                current_logger = logger
                
            safe_log(current_logger, 'debug', f"Monitoring function: {f.__name__}")
            safe_log(current_logger, 'debug', f"Arguments: {args}")

            try:
                start = time.time() * 1000  # Convert to milliseconds
                processed_args = args
                
                # Apply before middleware
                middlewares = get_middlewares()
                for middleware in middlewares:
                    if hasattr(middleware, 'before_call') and middleware.before_call:
                        try:
                            middleware_result = middleware.before_call(processed_args)
                            if middleware_result:
                                processed_args = middleware_result
                        except Exception as middleware_error:
                            safe_log(current_logger, 'debug', f"Middleware error: {middleware_error}")
                
                safe_log(current_logger, 'debug', f"Processed arguments: {processed_args}")

                # Execute the function
                function_error = None
                result = None
                        
                try:
                    result = await execute_func(f, *processed_args, **kwargs)
                    safe_log(current_logger, 'debug', f"Function executed successfully")
                except Exception as error:
                    function_error = error
                    safe_log(current_logger, 'debug', f"Function execution failed: {error}")
                    
                    # Handle error monitoring
                    await handle_error_monitoring(function_error, processed_args, options, start, current_logger)
                    raise function_error  # Re-raise the original error
                        
                # Handle success monitoring
                if function_error is None:
                    try:
                        await handle_success_monitoring(result, processed_args, options, start, current_logger)
                    except Exception as error:
                        safe_log(current_logger, 'debug', f"Error handling success monitoring: {error}")
                
                return result
                
            except Exception as error:
                safe_log(current_logger, 'error', f"Error: {error}")
                if function_error is not None:
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
                
                # Background monitoring for sync functions
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
                            def run_monitoring():
                                asyncio.run(async_wrapped_f(*args, **kwargs, potential_result=result))
                            
                            thread = threading.Thread(target=run_monitoring, daemon=True)
                            thread.start()
                    except Exception:
                        # If monitoring fails, don't affect the original function
                        pass
                
                # Start background monitoring
                fire_and_forget_monitoring()
                
                # Return the original result
                return result
            
            return sync_wrapped_f
    
    return wrap


async def handle_error_monitoring(error: Exception, processed_args: tuple, options: MonitorOptions, start: float, logger: logging.Logger):
    """Handle monitoring for function errors."""
    middlewares = get_middlewares()
    
    # Apply error middleware
    for middleware in middlewares:
        if hasattr(middleware, 'on_error') and middleware.on_error:
            try:
                middleware.on_error(error, processed_args)
            except Exception as middleware_error:
                safe_log(logger, 'debug', f"Error middleware failed: {middleware_error}")
                
    # Capture error data if onError handler is provided
    if options.send_on_function_error:
        try:
            error_info = await create_error_info(error, logger)
            
            chatId, email = await extract_user_info(options, logger)
                    
            payload = MonitorPayload(
                prompt="",
                response="",
                errorMessage=await to_string_api(error_info["error_message"]) + await to_string_api(error_info["stack_trace"]),
                chatId=chatId,
                email=email,
                shouldScore=False,
                tokens=0,
                requestTime=int(time.time() * 1000 - start),
                task=getattr(options, 'task', None),
                subTask=getattr(options, 'subTask', None)
            )
                    
            await send_to_api(payload, {
                "priority": "high"  # Errors always get high priority
            }, logger)
        except Exception as capture_error:
            safe_log(logger, 'debug', f"Error capture failed: {capture_error}")


async def handle_success_monitoring(result: Any, processed_args: tuple, options: MonitorOptions, start: float, logger: logging.Logger):
    """Handle monitoring for successful function execution."""
    middlewares = get_middlewares()
    
    # Apply afterCall middleware
    for middleware in middlewares:
        if hasattr(middleware, 'after_call') and middleware.after_call:
            try:
                middleware_result = middleware.after_call(result, processed_args)
                if middleware_result:
                    result = middleware_result
            except Exception as middleware_error:
                safe_log(logger, 'debug', f"After middleware failed: {middleware_error}")

    safe_log(logger, 'info', f"Result: {result}")
    
    # Capture success data
    if hasattr(options, 'capture') and options.capture:
        capture_result = options.capture(
            args=processed_args,
            result=result
        )
        
        # Process capture result with sanitization
        prompt, response = await process_capture_result(capture_result, options, logger)
        
        # Extract user information
        chatId, email = await extract_user_info(options, logger)

        payload = MonitorPayload(
            prompt=await to_string_api(prompt),
            response=await to_string_api(response),
            chatId=chatId if chatId else "anonymous",
            email=email if email else "anonymous@olakai.ai",
            shouldScore=getattr(options, 'shouldScore', False),
            tokens=0,
            requestTime=int(time.time() * 1000 - start),
            errorMessage=None,
            task=getattr(options, 'task', None),
            subTask=getattr(options, 'subTask', None)
        )

        safe_log(logger, 'info', f"Successfully defined payload: {payload}")
                
        # Send to API
        await send_to_api(payload, {
            "priority": getattr(options, 'priority', 'normal')
        }, logger) 