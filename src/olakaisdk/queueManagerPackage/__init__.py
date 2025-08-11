"""
Storage package for the Olakai SDK.

This package provides queue management and persistence functionality similar to the TypeScript implementation.
"""

from .queue_manager import (
    QueueManager,
    init_queue_manager,
    get_queue_manager,
    add_to_queue,
    flush_queue,
    get_queue_size,
    clear_queue,
)

__all__ = [
    "QueueManager",
    "init_queue_manager",
    "get_queue_manager",
    "add_to_queue",
    "flush_queue",
    "get_queue_size",
    "clear_queue",
]
