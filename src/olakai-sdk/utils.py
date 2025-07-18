import json
from typing import Any, Callable, List
import asyncio
from .types import MonitorOptions
from dataclasses import dataclass


def to_api_string(data: Any) -> str:
    """Convert data to API string format."""
    if isinstance(data, str):
        return data
    try:
        return json.dumps(data, default=str)
    except Exception:
        return str(data)

async def execute_func(f:Callable, *args, **kwargs) -> None:
    """Execute a function with arguments and return None."""
    try:
        if asyncio.iscoroutinefunction(f):
            await f(*args, **kwargs)
        else:
            f(*args, **kwargs)
    except Exception as e:
        raise e

@dataclass
class MonitorUtils:
    def capture_all_f(**kwargs):
        return {
            "input": kwargs["args"],
            "output": kwargs["result"]
        }
    capture_all = MonitorOptions(capture=capture_all_f)
    
    def capture_input_f(**kwargs):
        return {
            "input": kwargs["args"],
            "output": "Function executed successfully"
        }
    capture_input = MonitorOptions(capture=capture_input_f)

    def capture_output_f(**kwargs):
        return {
            "input": "Function called",
            "output": kwargs["result"]
        }
    capture_output = MonitorOptions(capture=capture_output_f)    