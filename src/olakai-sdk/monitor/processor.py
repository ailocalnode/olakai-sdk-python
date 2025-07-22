"""
Data processing and sanitization for the Olakai SDK monitor.
"""
import json
import re
import logging
from typing import Any, Optional, List
from ..shared.logger import get_default_logger, safe_log
from ..client.config import get_config


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
        logger = get_default_logger()
        
    if not patterns:
        return data
        
    config = await get_config()
    
    try:
        serialized = json.dumps(data, default=str)
        for pattern in patterns:
            serialized = pattern.sub("[REDACTED]", serialized)
        
        parsed = json.loads(serialized)

        safe_log(logger, 'info', "Data successfully sanitized")
        return parsed
    except Exception:
        safe_log(logger, 'debug', "Data failed to sanitize")
        return "[SANITIZED]"


async def process_capture_result(capture_result: dict, options, logger: Optional[logging.Logger] = None):
    """
    Process the result from a capture function, applying sanitization if needed.
    
    Args:
        capture_result: Result from the capture function
        options: Monitor options
        logger: Optional logger instance
        
    Returns:
        Processed prompt and response strings
    """
    if logger is None:
        logger = get_default_logger()
    
    prompt = capture_result.get("input", "")
    response = capture_result.get("output", "")

    safe_log(logger, 'info', f"Prompt: {prompt}")

    if getattr(options, 'sanitize', False):
        config = await get_config()
        sanitize_patterns = getattr(config, 'sanitize_patterns', None)
        prompt = await sanitize_data(prompt, sanitize_patterns, logger)
        response = await sanitize_data(response, sanitize_patterns, logger)

    safe_log(logger, 'info', f"Sanitized prompt: {prompt}")
    
    return prompt, response


async def extract_user_info(options, logger: Optional[logging.Logger] = None):
    """
    Extract chatId and email from options, handling both static values and callable functions.
    
    Args:
        options: Monitor options
        logger: Optional logger instance
        
    Returns:
        Tuple of (chatId, email)
    """
    if logger is None:
        logger = get_default_logger()
    
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
                safe_log(logger, 'debug', f"Error getting chatId")
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
                safe_log(logger, 'debug', f"Error getting email")
        else:
            email = options.email

    return chatId, email 