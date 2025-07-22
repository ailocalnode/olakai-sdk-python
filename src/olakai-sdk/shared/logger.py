"""
Logging utilities for the Olakai SDK using Python's built-in logging module.
"""

import logging
from typing import Optional


def get_default_logger() -> logging.Logger:
    """
    Get a default logger for the SDK if none is provided.
    
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger('[OlakaiSDK]')
    
    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


def safe_log(logger: Optional[logging.Logger], level: str, message: str) -> None:
    """
    Safely log a message with fallback to print if logger is None or fails.
    
    Args:
        logger: Logger instance (can be None)
        level: Log level ('debug', 'info', 'warning', 'error')
        message: Message to log
    """
    if logger is None:
        print(message)
        return
    
    try:
        getattr(logger, level.lower())(message)
    except Exception:
        # Fallback to print if logging fails
        print(message) 