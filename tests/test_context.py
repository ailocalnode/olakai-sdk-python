"""Tests for context module."""

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
        task="Support",
        subTask="password-reset",
        customData={"env": "prod", "region": "us", "tier": 3, "score": 0.95}
    ):
        context = get_current_context()
        assert context.userEmail == "user@example.com"
        assert context.task == "Support"
        assert context.subTask == "password-reset"
        assert context.customData == {"env": "prod", "region": "us", "tier": 3, "score": 0.95}


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
        with olakai_context(task="Task2", subTask="sub-123"):
            context = get_current_context()
            # Task should be overridden
            assert context.task == "Task2"
            # subTask should be added
            assert context.subTask == "sub-123"
            # userEmail should be inherited
            assert context.userEmail == "user1@example.com"


def test_context_merge_custom_data():
    """Test that customData is merged in nested contexts."""
    clear_context()

    with olakai_context(customData={"key1": "value1", "key2": "value2", "metric1": 1.0}):
        with olakai_context(customData={"key2": "override", "key3": "value3", "metric1": 2.5}):
            context = get_current_context()
            # Should merge dictionaries with child taking precedence
            assert context.customData == {
                "key1": "value1",
                "key2": "override",  # overridden
                "key3": "value3",    # added
                "metric1": 2.5       # overridden
            }


def test_context_to_dict():
    """Test OlakaiContextData.to_dict() method."""
    context_data = OlakaiContextData(
        userEmail="user@example.com",
        task="Test",
        customData={"key": "value"}
    )

    result = context_data.to_dict()
    assert result["userEmail"] == "user@example.com"
    assert result["task"] == "Test"
    assert result["customData"] == {"key": "value"}
    assert result["subTask"] is None


def test_context_data_merge():
    """Test OlakaiContextData.merge() method."""
    parent = OlakaiContextData(
        userEmail="parent@example.com",
        task="Parent Task",
        customData={"key1": "value1"}
    )

    child = OlakaiContextData(
        task="Child Task",
        customData={"key2": "value2"}
    )

    merged = parent.merge(child)

    # Child values take precedence
    assert merged.task == "Child Task"
    # Parent values are preserved if not in child
    assert merged.userEmail == "parent@example.com"
    # Dictionaries are merged
    assert merged.customData == {"key1": "value1", "key2": "value2"}


def test_context_empty():
    """Test context with no parameters."""
    clear_context()

    with olakai_context():
        context = get_current_context()
        assert context is not None
        assert context.userEmail is None
        assert context.task is None
        assert context.customData == {}


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
