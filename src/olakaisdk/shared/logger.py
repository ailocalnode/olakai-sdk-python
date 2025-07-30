"""
Logging utilities for the Olakai SDK using Python's built-in logging module.
"""

import logging


global_logger = None

def create_logger() -> logging.Logger:
    """
    Get a default logger for the SDK if none is provided.
    
    Returns:
        A configured logger instance
    """
    global global_logger
    if global_logger is None:
        global_logger = logging.getLogger('OlakaiSDK')
    
    # Only configure if not already configured
    if global_logger.name == 'OlakaiSDK' and not global_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        global_logger.addHandler(handler)
        global_logger.setLevel(logging.INFO)
    
    return global_logger

def set_logger_level(level: str) -> None:
    """
    Set the logger level.
    
    Args:
        level: Log level ('debug', 'info', 'warning', 'error')
    """
    global global_logger
    if global_logger is None:
        create_logger()
    global_logger.setLevel(level.upper())

def safe_log(level: str, message: str) -> None:
    """
    Safely log a message with fallback to print if logger is None or fails.
    
    Args:
        logger: Logger instance (can be None)
        level: Log level ('debug', 'info', 'warning', 'error')
        message: Message to log
    """
    global global_logger
    if global_logger is None:
        create_logger()
    
    try:
        if global_logger.name == 'OlakaiSDK':
            getattr(global_logger, level.lower())(message)
        else:
            getattr(global_logger, level.lower())(f"[OlakaiSDK]: {message}")
    except Exception:
        # Fallback to print if logging fails
        print(message) 