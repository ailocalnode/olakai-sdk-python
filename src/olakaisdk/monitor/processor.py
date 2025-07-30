"""
Data processing and sanitization for the Olakai SDK monitor.
"""
import json
import re
from typing import Any, Optional, List
from ..shared.logger import safe_log
from ..client.config import get_config
from .types import MonitorOptions
from ..client.types import ControlPayload
from ..client.api import send_to_api
from ..shared.exceptions import SanitizationError, ControlServiceError
from ..shared.types import ControlResponse


def sanitize_data(data: Any, patterns: Optional[List[re.Pattern]] = None) -> Any:
    """
    Sanitize data by replacing sensitive information with a placeholder.
    
    Args:
        data: The data to sanitize
        patterns: List of regex patterns to replace
        logger: Optional logger instance
        
    Returns:
        The sanitized data
    """
    if not patterns:
        return data
        
    try:
        serialized = json.dumps(data, default=str)
        for pattern in patterns:
            serialized = pattern.sub("[REDACTED]", serialized)
        
        parsed = json.loads(serialized)

        safe_log('info', "Data successfully sanitized")
        return parsed
    except Exception as e:
        safe_log('debug', f"Data failed to sanitize: {str(e)}")
        raise SanitizationError(f"Failed to sanitize data: {str(e)}") from e


def process_capture_result(capture_result: dict, options):
    """
    Process the result from a capture function, applying sanitization if needed.
    
    Args:
        capture_result: Result from the capture function
        options: Monitor options
        logger: Optional logger instance
        
    Returns:
        Processed prompt and response strings
    """
    prompt = capture_result.get("input", "")
    response = capture_result.get("output", "")

    safe_log('info', f"Prompt: {prompt}")

    if getattr(options, 'sanitize', False):
        config = get_config()
        sanitize_patterns = getattr(config, 'sanitize_patterns', None)
        try:
            prompt = sanitize_data(prompt, sanitize_patterns)
            response = sanitize_data(response, sanitize_patterns)
        except SanitizationError:
            safe_log('info', f"Sanitization failed, continuing anyway...")
    safe_log('info', f"Sanitized prompt: {prompt}")
    
    return prompt, response


def extract_user_info(options: MonitorOptions) -> tuple[str, str]:
    """
    Extract chatId and email from options, handling both static values and callable functions.
    
    Args:
        options: Monitor options
        logger: Optional logger instance
        
    Returns:
        Tuple of (chatId, email)
    """
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
                safe_log('debug', f"Error getting chatId")
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
                safe_log('debug', f"Error getting email")
        else:
            email = options.email

    return chatId, email 

async def should_allow_call(options: MonitorOptions, args: tuple, kwargs: dict) -> ControlResponse:
    """
    Check if the function should be blocked.
    
    Args:
        options: Monitor options
        logger: Optional logger instance
        
    Returns:
        True if the function should be blocked, False otherwise
        
    Raises:
        ControlServiceError: If control service communication fails
    """
    try:
        chatId, email = extract_user_info(options)

        prompt = "Args: " + str(args) + "\n\n Kwargs: " + json.dumps(kwargs) + "\n\n Task: " + (options.task if options.task else "") + "\n\n SubTask: " + (options.subTask if options.subTask else "")

        control_payload = ControlPayload(
            email=email,
            chatId=chatId,
            prompt=prompt,
            task=options.task,
            subTask=options.subTask,
            tokens=0,
            overrideControlCriteria=options.overrideControlCriteria if options.overrideControlCriteria else []
        )

        response = await send_to_api(control_payload)
        return response
    except Exception as e:
        safe_log('error', f"Control service failed: {str(e)}")
        raise ControlServiceError(f"Failed to check if function should be blocked: {str(e)}") from e