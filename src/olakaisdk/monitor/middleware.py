"""
Middleware management for the Olakai SDK monitor.
"""

from typing import List, Dict
from ..shared import safe_log, Middleware

# Global middleware registry for backward compatibility
_global_middlewares: List[Middleware] = []
# Instance-based middleware registry
_instance_middlewares: Dict[str, List[Middleware]] = {}


class MiddlewareManager:
    """Instance-based middleware manager."""

    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        if instance_id not in _instance_middlewares:
            _instance_middlewares[instance_id] = []

    def add_middleware(self, middleware: Middleware) -> None:
        """Add middleware to this instance."""
        _instance_middlewares[self.instance_id].append(middleware)
        safe_log(
            "info",
            f"Added middleware: {middleware.name} to instance {self.instance_id}",
        )

    def remove_middleware(self, name: str) -> None:
        """Remove middleware from this instance."""
        _instance_middlewares[self.instance_id] = [
            m for m in _instance_middlewares[self.instance_id] if m.name != name
        ]
        safe_log(
            "info",
            f"Removed middleware: {name} from instance {self.instance_id}",
        )

    def get_middlewares(self) -> List[Middleware]:
        """Get all registered middlewares for this instance."""
        return _instance_middlewares[self.instance_id].copy()


# Backward compatibility functions (deprecated)
def add_middleware(middleware: Middleware) -> None:
    """Add middleware to the global middleware registry."""
    _global_middlewares.append(middleware)
    safe_log(
        "warning",
        "Using deprecated global middleware. Consider using instance-based middleware.",
    )
    safe_log("info", f"Added middleware: {middleware.name}")


def remove_middleware(name: str) -> None:
    """Remove middleware from the global middleware registry."""
    global _global_middlewares
    _global_middlewares = [m for m in _global_middlewares if m.name != name]
    safe_log("info", f"Removed middleware: {name}")


def get_middlewares() -> List[Middleware]:
    """Get all registered middlewares."""
    return _global_middlewares
