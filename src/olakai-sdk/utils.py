import json
from typing import Any, Callable, List
import asyncio
from .types import Middleware


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