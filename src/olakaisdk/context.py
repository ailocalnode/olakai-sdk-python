"""Context manager for metadata injection into LLM telemetry."""

import contextvars
from typing import Dict, Optional, Union
from contextlib import contextmanager
from dataclasses import dataclass, field


# Thread-safe context storage using contextvars
_context_var = contextvars.ContextVar('olakai_context', default=None)


@dataclass
class OlakaiContextData:
    """
    Data stored in context for telemetry metadata.

    All fields are optional and will be merged with parent contexts
    when contexts are nested.
    """
    userEmail: Optional[str] = None
    userId: Optional[str] = None  # SDK client's user ID for tracking
    taskExecutionId: Optional[str] = None
    task: Optional[str] = None
    subTask: Optional[str] = None
    customData: Dict[str, Union[str, int, float, bool]] = field(default_factory=dict)

    def merge(self, other: 'OlakaiContextData') -> 'OlakaiContextData':
        """
        Merge with another context, where other takes precedence.

        Args:
            other: Context to merge with (takes priority)

        Returns:
            New OlakaiContextData with merged values
        """
        return OlakaiContextData(
            userEmail=other.userEmail or self.userEmail,
            userId=other.userId or self.userId,
            taskExecutionId=other.taskExecutionId or self.taskExecutionId,
            task=other.task or self.task,
            subTask=other.subTask or self.subTask,
            customData={**self.customData, **other.customData}
        )

    def to_dict(self) -> Dict:
        """
        Convert to dictionary for payload generation.

        Returns:
            Dictionary with non-None values
        """
        return {
            "userEmail": self.userEmail,
            "userId": self.userId,
            "taskExecutionId": self.taskExecutionId,
            "task": self.task,
            "subTask": self.subTask,
            "customData": self.customData if self.customData else None,
        }


@contextmanager
def olakai_context(
    userEmail: Optional[str] = None,
    userId: Optional[str] = None,
    taskExecutionId: Optional[str] = None,
    task: Optional[str] = None,
    subTask: Optional[str] = None,
    customData: Optional[Dict[str, Union[str, int, float, bool]]] = None
):
    """
    Context manager to add metadata to all LLM calls within scope.

    Contexts can be nested, with inner contexts overriding outer context
    values. The customData dictionary is merged with parent contexts.

    Args:
        userEmail: User email for tracking
        userId: SDK client's user ID for tracking
        taskExecutionId: Groups prompt requests by task execution
        task: High-level task category
        subTask: Specific subtask
        customData: Custom metadata (merged with parent)

    Example:
        >>> with olakai_context(userEmail="user@example.com", task="Support"):
        ...     # All OpenAI calls here will include this metadata
        ...     response = client.chat.completions.create(...)

        >>> # Nested contexts
        >>> with olakai_context(task="Support"):
        ...     with olakai_context(subTask="password-reset"):
        ...         # Inherits task="Support", adds subTask="password-reset"
        ...         response = client.chat.completions.create(...)
    """
    # Get current context (if nested)
    current = _context_var.get()

    # Create new context
    new_context = OlakaiContextData(
        userEmail=userEmail,
        userId=userId,
        taskExecutionId=taskExecutionId,
        task=task,
        subTask=subTask,
        customData=customData or {}
    )

    # Merge with parent context if exists
    if current:
        new_context = current.merge(new_context)

    # Set context
    token = _context_var.set(new_context)

    try:
        yield new_context
    finally:
        # Restore previous context
        _context_var.reset(token)


def get_current_context() -> Optional[OlakaiContextData]:
    """
    Get the current context data.

    This is used internally by instrumentation to access metadata.

    Returns:
        Current OlakaiContextData, or None if not in a context
    """
    return _context_var.get()


def clear_context() -> None:
    """
    Clear the current context.

    This is primarily for testing purposes.
    """
    token = _context_var.set(None)
