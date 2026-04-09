"""
Core simplified API for the Olakai SDK.
"""

import time
import asyncio
from typing import Callable, Dict, Any, Literal, Optional, Union
from .shared.types import OlakaiEventParams, MonitorPayload
from .client.api import send_to_api_simple
from .config import require_config


def olakai(params: OlakaiEventParams) -> None:
    """
    Track an event with the Olakai API.

    Args:
        params: Event parameters
    """
    config = require_config()

    # Convert to MonitorPayload for API compatibility
    payload = MonitorPayload(
        userEmail=params.userEmail or "anonymous@olakai.ai",
        chatId=params.sessionId or config.sessionId,
        taskExecutionId=params.taskExecutionId,
        prompt=params.prompt,
        response=params.response,
        tokens=params.tokens,
        requestTime=params.requestTime,
        task=params.task,
        subTask=params.subTask,
        customData=params.customData,
        shouldScore=params.shouldScore,
    )

    # Send asynchronously in background if possible, otherwise ignore
    try:
        loop = asyncio.get_running_loop()
        asyncio.create_task(send_to_api_simple(config, payload))
    except RuntimeError:
        # No event loop running, skip API call
        if config.debug:
            print(f"[Olakai SDK] Skipping API call - no event loop running")


def olakai_event(params: OlakaiEventParams) -> None:
    """
    Direct reporting function for simple event tracking.
    
    Args:
        params: The input data  
    """
    
    olakai(params)


FeedbackRating = Literal["UP", "DOWN"]


def olakai_feedback(
    session_id: str,
    rating: FeedbackRating,
    *,
    turn_index: Optional[int] = None,
    comment: Optional[str] = None,
    user_email: Optional[str] = None,
    custom_data: Optional[Dict[str, Union[str, int, float, bool, None]]] = None,
) -> None:
    """Report explicit user feedback on a prior agent interaction.

    Fire-and-forget, like ``olakai_event()``. Never raises — any
    configuration or transport errors are swallowed so that user
    code is not affected.

    Under the hood this sends a regular monitoring event with a
    well-known shape: a sentinel prompt of ``"[feedback]"`` and an
    empty response, tagged with ``eventType="feedback"`` and the
    feedback fields in ``customData``. The Olakai backend recognises
    this shape and routes it to the feedback surface.

    Args:
        session_id: The session/conversation ID of the interaction
            being rated. Should match the ``sessionId`` used when
            reporting the original event.
        rating: ``"UP"`` or ``"DOWN"`` — the user's feedback.
        turn_index: Optional zero-based turn index within the
            session, for turn-level feedback correlation.
        comment: Optional free-text comment alongside the rating.
        user_email: Optional override for the user who gave the
            feedback. Defaults to ``"anonymous@olakai.ai"`` when
            omitted, matching ``olakai_event()`` behaviour.
        custom_data: Optional customer-defined fields for domain
            context. Merged with the well-known feedback fields;
            caller-provided keys do not override the reserved
            ``eventType``/``feedbackRating``/``feedbackTurnIndex``/
            ``feedbackComment`` fields.

    Example:
        >>> olakai_feedback(
        ...     session_id="chat_abc123",
        ...     rating="UP",
        ...     turn_index=3,
        ...     comment="Very helpful answer",
        ... )
    """
    try:
        # Build the well-known feedback customData payload. We start
        # from the caller's custom_data (if any) so that our reserved
        # fields always take precedence over user-supplied keys.
        merged_custom_data: Dict[str, Union[str, int, float, bool, None]] = {}
        if custom_data:
            merged_custom_data.update(custom_data)

        merged_custom_data["eventType"] = "feedback"
        merged_custom_data["feedbackRating"] = rating
        if turn_index is not None:
            merged_custom_data["feedbackTurnIndex"] = turn_index
        if comment is not None:
            merged_custom_data["feedbackComment"] = comment

        params = OlakaiEventParams(
            prompt="[feedback]",
            response="",
            userEmail=user_email or "anonymous@olakai.ai",
            sessionId=session_id,
            customData=merged_custom_data,  # type: ignore[arg-type]
            shouldScore=False,
        )

        olakai(params)
    except Exception as e:  # noqa: BLE001 - fire-and-forget
        # Never raise from feedback reporting. Best-effort debug log
        # only if the SDK is configured with debug=True.
        try:
            from .config import get_config

            config = get_config()
            if config is not None and config.debug:
                print(f"[Olakai SDK] olakai_feedback failed: {e}")
        except Exception:
            pass


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
                    sessionId=options.get("sessionId"),
                    task=options.get("task"),
                    subTask=options.get("subTask"),
                    customData=options.get("customData"),
                    shouldScore=options.get("shouldScore", True),
                    tokens=0,
                    requestTime=int(time.time() * 1000 - start_time),
                )

                # Track the event
                olakai(params)

                return result

            except Exception as e:
                # Track error event
                params = OlakaiEventParams(
                    prompt=str(args) + str(kwargs),
                    response=f"Error: {str(e)}",
                    userEmail=options.get("userEmail", "anonymous@olakai.ai"),
                    sessionId=options.get("sessionId"),
                    task=options.get("task"),
                    subTask=options.get("subTask"),
                    customData=options.get("customData"),
                    shouldScore=options.get("shouldScore", True),
                    tokens=0,
                    requestTime=int(time.time() * 1000 - start_time),
                )

                olakai(params)
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
                    sessionId=options.get("sessionId"),
                    task=options.get("task"),
                    subTask=options.get("subTask"),
                    customData=options.get("customData"),
                    shouldScore=options.get("shouldScore", True),
                    tokens=0,
                    requestTime=int(time.time() * 1000 - start_time),
                )

                # Track the event
                olakai(params)

                return result

            except Exception as e:
                # Track error event
                params = OlakaiEventParams(
                    prompt=str(args) + str(kwargs),
                    response=f"Error: {str(e)}",
                    userEmail=options.get("userEmail", "anonymous@olakai.ai"),
                    sessionId=options.get("sessionId"),
                    task=options.get("task"),
                    subTask=options.get("subTask"),
                    customData=options.get("customData"),
                    shouldScore=options.get("shouldScore", True),
                    tokens=0,
                    requestTime=int(time.time() * 1000 - start_time),
                )

                olakai(params)
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


