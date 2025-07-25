"""
Core monitoring decorator functionality.
"""
import asyncio
import socket
import inspect
import time
import threading
from dataclasses import fields
from typing import Any, Callable
from .types import MonitorOptions
from .middleware import get_middlewares
from .processor import process_capture_result, extract_user_info, should_block
from ..client.types import MonitorPayload
from ..client.api import send_to_api
from ..shared.utils import create_error_info, to_string_api
from ..shared.logger import safe_log
from ..shared.exceptions import OlakaiFunctionBlocked, MiddlewareError, ControlServiceError

externalLogic = False


def olakai_monitor(**kwargs):
    """
    Monitor a function with the given options.
    
    Kwargs:
        possible options (must be kwargs):
            capture: Callable
            sanitize: bool
            send_on_function_error: bool
            priority: str
            email: str
            chatId: str
            shouldScore: bool
            task: str
            subTask: str
            controlOptions: ControlOptions
        
    Returns:
        Decorator function
    """
    options = MonitorOptions()
    if len(kwargs) > 0:
        fields_names = [field.name for field in fields(MonitorOptions)]
        for key, value in kwargs.items():
            if key in fields_names:
                try:
                    setattr(options, key, value)
                except Exception as e:
                    safe_log('debug', f"Error setting attribute, check the type of the value: {e}")
            else:
                safe_log('debug', f"Invalid keyword argument: {key}")

    def wrap(f: Callable) -> Callable:

        
        async def async_wrapped_f(*args, **kwargs):
            safe_log('debug', f"Monitoring function: {f.__name__}")
            safe_log('debug', f"Arguments: {args}")

            try:
                #TODO modify the del[potential_result] to behave well with shouldBlock
                start = time.time() * 1000  # Convert to milliseconds
                processed_args = args
                processed_kwargs = kwargs
                if "potential_result" in kwargs:
                    del kwargs["potential_result"]
                
                # Check if the function should be blocked
                should_be_blocked = await should_block(options, args, kwargs)
                if should_be_blocked:
                    safe_log('warning', f"Function {f.__name__} was blocked")
                    raise OlakaiFunctionBlocked("Function execution blocked by Olakai")

                # Apply before middleware
                try:
                    processed_args, processed_kwargs = apply_before_middleware(processed_args, processed_kwargs)
                except MiddlewareError:
                    pass
                
                safe_log('info', f"Processed arguments: {processed_args}, \n Processed kwargs: {processed_kwargs}")

                # Execute the function
                function_error = None
                result = None
                        
                try:
                    result = await f(*processed_args, **processed_kwargs)
                    safe_log('debug', f"Function executed successfully")
                except Exception as error:
                    function_error = error
                    safe_log('debug', f"Function execution failed: {error}")
                    
                    # Handle error monitoring
                    handle_error_monitoring(function_error, processed_args, processed_kwargs, options, start)
                    raise function_error  # Re-raise the original error
                        
                # Handle success monitoring
                if function_error is None:
                    try:
                        handle_success_monitoring(result, processed_args, processed_kwargs, options, start)
                    except Exception as error:
                        safe_log('debug', f"Error handling success monitoring: {error}")
                
                return result
            

            except OlakaiFunctionBlocked as e:
                # Re-raise blocking exceptions without modification
                raise e
            except Exception as error:
                safe_log('error', f"Error: {error}")
                if function_error is not None:
                    raise function_error
                result = await f(*args, **kwargs)
                return result
        
        def sync_wrapped_f(*args, **kwargs):
            safe_log('debug', f"Monitoring sync function: {f.__name__}")
            safe_log('info', f"Arguments: {args}, \n Kwargs: {kwargs}")
            
            # Check if the function should be blocked
            should_be_blocked = False
            try:
                loop = asyncio.get_running_loop()
                # If there's a running loop, we need to run should_block in a separate thread
                # to avoid blocking the current thread
                import concurrent.futures
                
                def run_should_block():
                    return asyncio.run(should_block(options, args, kwargs))
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_should_block)
                    should_be_blocked = future.result()
                    
            except RuntimeError:
                # No running loop, create a new one
                should_be_blocked = asyncio.run(should_block(options, args, kwargs))

            except ControlServiceError:
                safe_log('debug', f"Control service error")
                should_be_blocked = True

            except Exception as e:
                safe_log('debug', f"Error checking should_block: {e}")
                # If checking fails, default to blocking
                should_be_blocked = True
                
            # If the function should be blocked, don't execute it
            if should_be_blocked:
                safe_log('warning', f"Function {f.__name__} was blocked")
                raise OlakaiFunctionBlocked("Function execution blocked by Olakai")
            
            def dump_stack_with_args(limit=20, filter=["/site-packages/", "\\site-packages\\", "asyncio"], sanitize_args=["api_key"]):
                stack = inspect.stack()
                call_info = []
                for frame_info in stack[:limit]:
                    frame = frame_info.frame
                    filename = frame_info.filename
                    if any(filter in filename for filter in filter):
                        continue
                    func = frame_info.function
                    args, _, _, values = inspect.getargvalues(frame)
                    arg_str = ", ".join(
                        f"{a}={repr(values[a])[:50]}" if (a in values and a not in sanitize_args) else f"{a}=[REDACTED]"
                        for a in args
                    )
                    call_info.append({
                        "filename": filename.split('\\' if '\\' in filename else '/')[-1],
                        "lineno": frame_info.lineno,
                        "function": func,
                        "args": arg_str
                    })
                return call_info

            if externalLogic:
                original_connect = socket.socket.connect
                def monitored_connect(self, address):
                    print(f"[NETWORK] Connecting to {address}")
                    stack = dump_stack_with_args()
                    nice_trace = ""
                    for call in reversed(stack):
                        nice_trace += f"{call['function']}({call['args']}) -> "
                    nice_trace = nice_trace[:-4]
                    nice_trace += "\n ===============================\n"
                    print(nice_trace)
                    print("stack trace:")
                    for call in stack:
                        print(f"{call['filename']}:{call['lineno']} {call['function']}({call['args']})")
                    return original_connect(self, address)
                
                socket.socket.connect = monitored_connect
                
            try:
                result = f(*args, **kwargs)
            except Exception as error:
                raise error
            finally:
                if externalLogic:
                    socket.socket.connect = original_connect
                # Background monitoring for sync functions
            def fire_and_forget_monitoring():
                        
                try:
                    # Check if there's already an event loop running
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
                    safe_log('debug', f"Monitoring failed")
                    pass
                
                # Start background monitoring
            fire_and_forget_monitoring()
                
                # Return the original result
            return result

            

        # Check if the decorated function is async or sync
        if asyncio.iscoroutinefunction(f):
            # For async functions, return the async wrapper directly
            return async_wrapped_f
        else:
            # For sync functions, create a sync wrapper that fires off monitoring in background
            return sync_wrapped_f
    
    return wrap

def apply_before_middleware(args: tuple, kwargs: dict):
    """Apply before middleware to the function."""
    safe_log('debug', f"Applying before middleware to the function")
    processed_args = args
    processed_kwargs = kwargs
    middlewares = get_middlewares()
    for middleware in middlewares:
        if hasattr(middleware, 'before_call') and middleware.before_call:
            try:
                safe_log('info', f"Applying before middleware: {middleware.__class__.__name__}")
                processed_args, processed_kwargs = middleware.before_call(args, kwargs)
                safe_log('info', f"Processed arguments: {processed_args}")
                safe_log('info', f"Processed kwargs: {processed_kwargs}")
            except MiddlewareError as e:
                safe_log('debug', f"Middleware error: {e}")
                raise e
    safe_log('info', f"Exiting apply_before_middleware")
    return processed_args, processed_kwargs


async def handle_error_monitoring(error: Exception, processed_args: tuple, processed_kwargs: dict, options: MonitorOptions, start: float):
    """Handle monitoring for function errors."""
    middlewares = get_middlewares()
    
    # Apply error middleware
    for middleware in middlewares:
        if hasattr(middleware, 'on_error') and middleware.on_error:
            try:
                middleware.on_error(error, processed_args, processed_kwargs)
            except Exception as middleware_error:
                safe_log('debug', f"Error middleware failed: {middleware_error}")
                
    # Capture error data if onError handler is provided
    if options.send_on_function_error:
        try:
            error_info = await create_error_info(error)
            
            chatId, email = await extract_user_info(options)
                    
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
            })
        except Exception as capture_error:
            safe_log('debug', f"Error capture failed: {capture_error}")


async def handle_success_monitoring(result: Any, processed_args: tuple, processed_kwargs: dict, options: MonitorOptions, start: float):
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
                safe_log('debug', f"After middleware failed: {middleware_error}")

    safe_log('info', f"Result: {result}")
    
    # Capture success data
    if hasattr(options, 'capture') and options.capture:
        capture_result = options.capture(
            args=processed_args,
            kwargs=processed_kwargs,
            result=result
        )
        
        # Process capture result with sanitization
        prompt, response = await process_capture_result(capture_result, options)
        
        # Extract user information
        chatId, email = await extract_user_info(options)

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

        safe_log('info', f"Successfully defined payload: {payload}")
                
        # Send to API
        await send_to_api(payload, {
            "priority": getattr(options, 'priority', 'normal')
        }) 