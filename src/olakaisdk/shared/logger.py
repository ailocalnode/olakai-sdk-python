"""
Logging utilities for the Olakai SDK using Python's built-in logging module.
"""

import logging
from ..client.config import get_config


def get_default_logger() -> logging.Logger:
    """
    Get a default logger for the SDK if none is provided.
    
    Returns:
        A configured logger instance
    """
    config = get_config()
    logger = config.logger
    
    # Only configure if not already configured
    if logger.name == 'OlakaiSDK' and not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


def safe_log(level: str, message: str) -> None:
    """
    Safely log a message with fallback to print if logger is None or fails.
    
    Args:
        logger: Logger instance (can be None)
        level: Log level ('debug', 'info', 'warning', 'error')
        message: Message to log
    """
    logger = get_default_logger()
    
    try:
        if logger.name == 'OlakaiSDK':
            getattr(logger, level.lower())(message)
        else:
            getattr(logger, level.lower())(f"[OlakaiSDK]: {message}")
    except Exception:
        # Fallback to print if logging fails
        print(message) 