"""Tests for context module."""

import pytest
from src.olakaisdk.context import (
    olakai_context,
    get_current_context,
    clear_context,
    OlakaiContextData
)


def test_context_basic():
    """Test basic context manager usage."""
    clear_context()

    with olakai_context(userEmail="test@example.com", task="Test Task"):
        context = get_current_context()
        assert context is not None
        assert context.userEmail == "test@example.com"
        assert context.task == "Test Task"

    # Context should be cleared after exiting
    context = get_current_context()
    assert context is None


def test_context_all_fields():
    """Test context with all fields populated."""
    clear_context()

    with olakai_context(
        userEmail="user@example.com",
        chatId="chat-123",
        task="Support",
        subTask="password-reset",
        customDimensions={"env": "prod", "region": "us"},
        customMetrics={"tier": 3.0, "score": 0.95}
    ):
        context = get_current_context()
        assert context.userEmail == "user@example.com"
        assert context.chatId == "chat-123"
        assert context.task == "Support"
        assert context.subTask == "password-reset"
        assert context.customDimensions == {"env": "prod", "region": "us"}
        assert context.customMetrics == {"tier": 3.0, "score": 0.95}


def test_context_nested():
    """Test nested contexts with inheritance."""
    clear_context()

    with olakai_context(userEmail="user@example.com", task="Parent"):
        parent_context = get_current_context()
        assert parent_context.task == "Parent"
        assert parent_context.userEmail == "user@example.com"

        with olakai_context(subTask="Child"):
            child_context = get_current_context()
            # Should inherit parent values
            assert child_context.task == "Parent"
            assert child_context.userEmail == "user@example.com"
            # And add new values
            assert child_context.subTask == "Child"

        # After exiting child, should be back to parent
        back_to_parent = get_current_context()
        assert back_to_parent.task == "Parent"
        assert back_to_parent.subTask is None


def test_context_nested_override():
    """Test nested contexts can override parent values."""
    clear_context()

    with olakai_context(task="Task1", userEmail="user1@example.com"):
        with olakai_context(task="Task2", chatId="chat-123"):
            context = get_current_context()
            # Task should be overridden
            assert context.task == "Task2"
            # chatId should be added
            assert context.chatId == "chat-123"
            # userEmail should be inherited
            assert context.userEmail == "user1@example.com"


def test_context_merge_dimensions():
    """Test that customDimensions are merged in nested contexts."""
    clear_context()

    with olakai_context(customDimensions={"dim1": "value1", "dim2": "value2"}):
        with olakai_context(customDimensions={"dim2": "override", "dim3": "value3"}):
            context = get_current_context()
            # Should merge dictionaries with child taking precedence
            assert context.customDimensions == {
                "dim1": "value1",
                "dim2": "override",  # overridden
                "dim3": "value3"     # added
            }


def test_context_merge_metrics():
    """Test that customMetrics are merged in nested contexts."""
    clear_context()

    with olakai_context(customMetrics={"metric1": 1.0, "metric2": 2.0}):
        with olakai_context(customMetrics={"metric2": 2.5, "metric3": 3.0}):
            context = get_current_context()
            # Should merge dictionaries with child taking precedence
            assert context.customMetrics == {
                "metric1": 1.0,
                "metric2": 2.5,  # overridden
                "metric3": 3.0   # added
            }


def test_context_to_dict():
    """Test OlakaiContextData.to_dict() method."""
    context_data = OlakaiContextData(
        userEmail="user@example.com",
        task="Test",
        customDimensions={"key": "value"}
    )

    result = context_data.to_dict()
    assert result["userEmail"] == "user@example.com"
    assert result["task"] == "Test"
    assert result["customDimensions"] == {"key": "value"}
    assert result["chatId"] is None
    assert result["subTask"] is None


def test_context_data_merge():
    """Test OlakaiContextData.merge() method."""
    parent = OlakaiContextData(
        userEmail="parent@example.com",
        task="Parent Task",
        customDimensions={"dim1": "value1"}
    )

    child = OlakaiContextData(
        task="Child Task",
        customDimensions={"dim2": "value2"}
    )

    merged = parent.merge(child)

    # Child values take precedence
    assert merged.task == "Child Task"
    # Parent values are preserved if not in child
    assert merged.userEmail == "parent@example.com"
    # Dictionaries are merged
    assert merged.customDimensions == {"dim1": "value1", "dim2": "value2"}


def test_context_empty():
    """Test context with no parameters."""
    clear_context()

    with olakai_context():
        context = get_current_context()
        assert context is not None
        assert context.userEmail is None
        assert context.chatId is None
        assert context.task is None
        assert context.customDimensions == {}
        assert context.customMetrics == {}


def test_get_current_context_when_none():
    """Test get_current_context returns None when not in context."""
    clear_context()

    context = get_current_context()
    assert context is None


def test_clear_context():
    """Test clear_context clears the context."""
    with olakai_context(userEmail="test@example.com"):
        assert get_current_context() is not None

    clear_context()
    assert get_current_context() is None


def test_context_exception_handling():
    """Test that context is properly cleared even if exception occurs."""
    clear_context()

    try:
        with olakai_context(userEmail="test@example.com"):
            assert get_current_context() is not None
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Context should still be cleared
    assert get_current_context() is None
