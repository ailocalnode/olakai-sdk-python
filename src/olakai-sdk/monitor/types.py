"""
Types specific to monitoring functionality.
"""
from dataclasses import dataclass
from typing import Optional, Callable, Union

@dataclass 
class Middleware:
    """Middleware for monitoring functions."""
    name: str
    before_call: Optional[Callable] = None
    after_call: Optional[Callable] = None
    on_error: Optional[Callable] = None

@dataclass
class MonitorUtils:
    """Utility functions for data capture in monitoring."""
    
    @staticmethod
    def capture_all_f(**kwargs):
        """Capture all input and output data."""
        return {
            "input": kwargs["args"],
            "output": kwargs["result"]
        }
    
    @staticmethod
    def capture_input_f(**kwargs):
        """Capture only input data."""
        return {
            "input": kwargs["args"],
            "output": "Function executed successfully"
        }

    @staticmethod
    def capture_output_f(**kwargs):
        """Capture only output data."""
        return {
            "input": "Function called",
            "output": kwargs["result"]
        } 

@dataclass
class MonitorOptions:
    """Options for monitoring functions."""
    capture: Optional[Callable] = MonitorUtils.capture_all_f  # Will be set to default in helpers.py
    sanitize: bool = False
    on_error: Optional[Callable] = None
    priority: str = "normal"
    email: Optional[Union[str, Callable]] = "anonymous@olakai.ai"
    chatId: Optional[Union[str, Callable]] = "123"
    shouldScore: bool = False
    task: Optional[str] = None
    subTask: Optional[str] = None