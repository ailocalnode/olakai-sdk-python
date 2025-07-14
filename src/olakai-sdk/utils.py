import json
from typing import Any


def to_api_string(data: Any) -> str:
    """Convert data to API string format."""
    if isinstance(data, str):
        return data
    try:
        return json.dumps(data, default=str)
    except Exception:
        return str(data)