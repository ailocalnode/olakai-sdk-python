"""Basic tests for the olakaisdk package."""
from olakaisdk import __version__


def test_version():
    """Test that version is accessible."""
    assert __version__ == "0.1.1"


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