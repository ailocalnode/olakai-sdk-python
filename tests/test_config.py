"""Tests for config module."""

import pytest
from src.olakaisdk.config import (
    olakai_config,
    get_config,
    require_config,
    is_initialized
)
from src.olakaisdk.shared.exceptions import APIKeyMissingError


def test_olakai_config_basic():
    """Test basic configuration."""
    olakai_config("test-api-key", "https://test.olakai.ai", debug=False)

    config = get_config()
    assert config is not None
    assert config.api_key == "test-api-key"
    assert config.endpoint == "https://test.olakai.ai"
    assert config.debug is False


def test_olakai_config_defaults():
    """Test configuration with default values."""
    olakai_config("test-key")

    config = get_config()
    assert config is not None
    assert config.api_key == "test-key"
    assert config.endpoint == "https://app.olakai.ai"
    assert config.debug is False


def test_olakai_config_debug_mode():
    """Test configuration with debug mode enabled."""
    olakai_config("test-key", debug=True)

    config = get_config()
    assert config is not None
    assert config.debug is True


def test_olakai_config_missing_api_key():
    """Test that missing API key raises error."""
    with pytest.raises(APIKeyMissingError, match="API key is required"):
        olakai_config("")

    with pytest.raises(APIKeyMissingError, match="API key is required"):
        olakai_config(None)


def test_get_config():
    """Test get_config returns current configuration."""
    olakai_config("test-key", "https://example.com")

    config = get_config()
    assert config is not None
    assert config.api_key == "test-key"
    assert config.endpoint == "https://example.com"


def test_require_config_when_initialized():
    """Test require_config returns config when initialized."""
    olakai_config("test-key")

    config = require_config()
    assert config is not None
    assert config.api_key == "test-key"


def test_require_config_when_not_initialized():
    """Test require_config raises error when not initialized."""
    # Reset global config
    import src.olakaisdk.config as config_module
    config_module._global_config = None

    with pytest.raises(RuntimeError, match="not initialized"):
        require_config()


def test_is_initialized():
    """Test is_initialized returns correct status."""
    # Reset global config
    import src.olakaisdk.config as config_module
    config_module._global_config = None

    assert is_initialized() is False

    olakai_config("test-key")
    assert is_initialized() is True


def test_config_can_be_reconfigured():
    """Test that config can be updated with new values."""
    olakai_config("key1", "https://endpoint1.com")
    config = get_config()
    assert config.api_key == "key1"

    olakai_config("key2", "https://endpoint2.com")
    config = get_config()
    assert config.api_key == "key2"
    assert config.endpoint == "https://endpoint2.com"
