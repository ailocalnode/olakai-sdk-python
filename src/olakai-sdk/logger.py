"""
Logging utilities for the Olakai SDK using Python's built-in logging module.
"""

import logging

# Create a logger for the SDK
sdk_logger = logging.getLogger('olakai-sdk')

def setup_logging(level=logging.INFO):
    """
    Setup logging configuration for the SDK.
    
    Args:
        level: Logging level (default: INFO)
    """
    # Only configure if not already configured
    if not sdk_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        sdk_logger.addHandler(handler)
        sdk_logger.setLevel(level)

def get_logger():
    """Get the SDK logger instance."""
    return sdk_logger 