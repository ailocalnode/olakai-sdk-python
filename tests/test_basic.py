"""Basic tests for the olakaisdk package."""

import pytest
import asyncio
from unittest.mock import Mock
from olakaisdk import __version__


def test_version():
    """Test that version is accessible."""
    assert __version__ == "0.1.0"


def test_import():
    """Test that main functions can be imported."""
    from olakaisdk import init_client, olakai_monitor

    assert callable(init_client)
    assert callable(olakai_monitor)


def test_monitor_decorator():
    """Test that the monitor decorator can be applied."""
    from olakaisdk import olakai_monitor

    @olakai_monitor()
    def test_function(x: int) -> int:
        return x * 2

    # Test that the function still works when wrapped
    result = test_function(5)
    assert result == 10


def test_config_types():
    """Test that types can be imported."""
    from olakaisdk import SDKConfig, MonitorOptions

    # Test basic instantiation
    config = SDKConfig(apiKey="test", apiUrl="https://test.com")
    assert config.apiKey == "test"

    monitor_opts = MonitorOptions(task="test-task")
    assert monitor_opts.task == "test-task"


def test_middleware_management():
    """Test middleware addition and removal."""
    from olakaisdk import add_middleware, remove_middleware, Middleware
    from olakaisdk.monitor.middleware import middlewares

    # Clear any existing middlewares
    middlewares.clear()

    # Create test middleware
    test_middleware = Middleware(name="test_middleware")

    # Test adding middleware
    asyncio.run(add_middleware(test_middleware))
    assert len(middlewares) == 1
    assert middlewares[0].name == "test_middleware"

    # Test removing middleware
    asyncio.run(remove_middleware("test_middleware"))
    assert len(middlewares) == 0


def test_sdk_config_defaults():
    """Test SDKConfig with default values."""
    from olakaisdk import SDKConfig

    config = SDKConfig()
    assert config.apiKey == ""
    assert config.batchSize == 10
    assert config.timeout == 20000
    assert config.enableLocalStorage == True
    assert config.debug == False


def test_monitor_options_defaults():
    """Test MonitorOptions with default values."""
    from olakaisdk import MonitorOptions

    options = MonitorOptions()
    assert options.sanitize == False
    assert options.send_on_function_error == True
    assert options.priority == "normal"
    assert options.shouldScore == False


@pytest.mark.asyncio
async def test_init_client_basic():
    """Test basic client initialization."""
    from olakaisdk import init_client, get_config

    # Test initialization
    await init_client(api_key="test_key", domain="https://test.example.com")

    config = get_config()
    assert config.apiKey == "test_key"
    assert config.apiUrl == "https://test.example.com/api/monitoring/prompt"


@pytest.mark.asyncio
async def test_init_client_with_kwargs():
    """Test client initialization with additional kwargs."""
    from olakaisdk import init_client, get_config

    # Test initialization with kwargs
    await init_client(
        api_key="test_key2",
        domain="https://test2.example.com",
        debug=True,
        batchSize=5,
    )

    config = get_config()
    assert config.apiKey == "test_key2"
    assert config.debug == True
    assert config.batchSize == 5


def test_async_monitor_decorator():
    """Test monitor decorator with async functions."""
    from olakaisdk import olakai_monitor

    @olakai_monitor()
    async def async_test_function(x: int) -> int:
        return x * 3

    # Test that the async function still works when wrapped
    result = asyncio.run(async_test_function(4))
    assert result == 12


def test_monitor_decorator_with_options():
    """Test monitor decorator with custom options."""
    from olakaisdk import olakai_monitor, MonitorOptions

    options = MonitorOptions(task="custom-task", shouldScore=True)

    @olakai_monitor(options)
    def test_function_with_options(x: int) -> int:
        return x + 10

    result = test_function_with_options(5)
    assert result == 15


def test_monitor_decorator_error_handling():
    """Test that monitor decorator doesn't break error propagation."""
    from olakaisdk import olakai_monitor

    @olakai_monitor()
    def error_function():
        raise ValueError("Test error")

    # Test that errors are still raised
    with pytest.raises(ValueError, match="Test error"):
        error_function()


@pytest.mark.asyncio
async def test_to_string_api():
    """Test the to_string_api utility function."""
    from olakaisdk.shared.utils import to_string_api

    # Test various data types
    assert await to_string_api(None) == "Empty data"
    assert await to_string_api("") == "Empty data"
    assert await to_string_api("test string") == "test string"
    assert await to_string_api([1, 2, 3]) == "123"
    assert await to_string_api({"key": "value"}) == '{"key": "value"}'


def test_middleware_type():
    """Test Middleware type creation."""
    from olakaisdk import Middleware

    # Test with callbacks
    before_callback = Mock()
    after_callback = Mock()

    middleware = Middleware(
        name="test", before_call=before_callback, after_call=after_callback
    )

    assert middleware.name == "test"
    assert middleware.before_call == before_callback
    assert middleware.after_call == after_callback


@pytest.mark.asyncio
async def test_config_get():
    """Test get_config function."""
    from olakaisdk import get_config, init_client

    # Initialize with specific config
    await init_client(api_key="config_test_key")

    config = get_config()
    assert config.apiKey == "config_test_key"
    assert hasattr(config, "apiUrl")
    assert hasattr(config, "batchSize")
    assert hasattr(config, "timeout")


def test_all_exports():
    """Test that all expected exports are available."""
    import olakaisdk

    expected_exports = [
        "init_client",
        "olakai_monitor",
        "get_config",
        "add_middleware",
        "remove_middleware",
        "SDKConfig",
        "MonitorOptions",
        "Middleware",
        "MonitorUtils",
    ]

    for export in expected_exports:
        assert hasattr(olakaisdk, export), f"Missing export: {export}"


@pytest.mark.asyncio
async def test_sanitize_data():
    """Test data sanitization functionality."""
    from olakaisdk.monitor.processor import sanitize_data
    import re

    # Test without patterns
    data = {"password": "secret123"}
    result = await sanitize_data(data)
    assert result == data  # Should return unchanged without patterns

    # Test with patterns
    patterns = [re.compile(r"secret\d+")]
    result = await sanitize_data(data, patterns)
    # Should replace the sensitive data
    assert result != data


def test_monitor_utils_import():
    """Test that MonitorUtils can be imported and used."""
    from olakaisdk import MonitorUtils

    # Test that MonitorUtils has expected attributes
    assert hasattr(MonitorUtils, "capture_all_f")
