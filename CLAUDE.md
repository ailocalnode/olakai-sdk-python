# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Olakai Python SDK is a monitoring and tracking SDK for AI/ML applications. It provides a decorator-based approach to monitor function calls and send telemetry data to the Olakai API. The SDK underwent a major simplification in v0.4.0, moving from complex configuration to a simple `olakai_config()` + `@olakai_monitor()` pattern.

**Key Concepts:**
- **Decorator-based monitoring**: Wrap any function with `@olakai_monitor()` to track inputs/outputs
- **Async-first architecture**: API calls are made asynchronously to avoid blocking user functions
- **Telemetry payloads**: Track prompts, responses, user emails, chat IDs, tasks, and custom dimensions/metrics
- **Global configuration**: Single `olakai_config()` call initializes SDK for entire application

## Commands

### Development Setup
```bash
# Install with development dependencies
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_basic.py

# Run specific test
pytest tests/test_basic.py::test_version

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Run all checks (formatting, linting, type checking, tests)
./tests/check.sh

# Format code with ruff
ruff format --line-length 80 src/olakaisdk tests

# Lint with ruff
ruff check --fix src/olakaisdk tests

# Type check with mypy
mypy --ignore-missing-imports src/olakaisdk tests
```

### Building & Publishing
```bash
# Build distribution packages
python -m build

# Check built packages
twine check dist/*

# Upload to PyPI (requires credentials)
twine upload dist/*
```

## Architecture

### Module Structure

```
src/olakaisdk/
├── __init__.py           # Public API exports
├── core.py               # Main API: olakai_config, olakai_monitor, olakai, olakai_report
├── monitor/              # Decorator implementation
│   ├── __init__.py
│   └── decorator.py      # olakai_monitor decorator with sync/async support
├── client/               # API communication
│   ├── __init__.py
│   ├── api.py            # HTTP client with retry logic
│   └── client.py         # (if exists)
└── shared/               # Common types and exceptions
    ├── __init__.py
    ├── types.py          # Dataclasses: OlakaiConfig, OlakaiEventParams, MonitorPayload, etc.
    └── exceptions.py     # Custom exceptions
```

### Key Files

**`src/olakaisdk/core.py`**
- Global configuration management via `_global_config`
- `olakai_config()`: Initialize SDK with API key and endpoint
- `olakai_monitor()`: Decorator factory that wraps functions for monitoring
- `olakai()`: Low-level event tracking function
- `olakai_report()`: Direct reporting without decorators
- Handles both sync and async functions by detecting with `asyncio.iscoroutinefunction()`

**`src/olakaisdk/monitor/decorator.py`**
- Alternative implementation of `olakai_monitor` (both exist for compatibility)
- Sync wrapper uses `asyncio.create_task()` to fire-and-forget API calls
- Async wrapper uses `await` for API calls
- Error handling: captures exceptions, reports them, then re-raises

**`src/olakaisdk/client/api.py`**
- `make_api_call()`: Core HTTP POST to `/api/monitoring/prompt` or `/api/control/prompt`
- `send_with_retry()`: Exponential backoff retry logic (max 3 retries)
- `send_to_api_simple()`: Simplified interface for monitoring payloads
- Uses `requests` library for HTTP calls

**`src/olakaisdk/shared/types.py`**
- `OlakaiConfig`: SDK configuration (api_key, endpoint, debug)
- `OlakaiEventParams`: Event parameters for tracking (prompt, response, userEmail, chatId, task, subTask, customDimensions, customMetrics)
- `MonitorPayload`: API payload structure
- `MonitorOptions`: Decorator options
- `APIResponse`, `ControlResponse`: API response types

### Design Patterns

**Global Singleton Configuration**
- `_global_config` in `core.py` holds SDK state
- All monitoring functions reference this global config
- `get_config()` provides read-only access

**Decorator Factory Pattern**
- `olakai_monitor()` can be used as `@olakai_monitor` or `@olakai_monitor(task="...")`
- Uses `fn is None` check to distinguish between `@decorator` and `@decorator(args)`

**Async/Sync Dual Support**
- Decorators check `asyncio.iscoroutinefunction()` to determine function type
- Sync functions get wrapped with background `asyncio.create_task()` calls
- Async functions properly await API calls

**Fire-and-Forget Monitoring**
- Monitoring should never block user functions
- API calls happen asynchronously in background
- Errors in monitoring are logged but don't propagate to user code (except in tests)

## Important Implementation Details

### Dynamic Parameters with Lambdas
The SDK supports lambda functions for dynamic parameter resolution:
```python
@olakai_monitor(
    userEmail=lambda args: get_user_email(args[0]),
    chatId=lambda args: get_session_id(args[0])
)
```
This is mentioned in README but not fully implemented in current code - the decorator currently evaluates options at decoration time, not call time.

### Custom Dimensions and Metrics
- `customDimensions`: Dict[str, str] - categorical/string metadata (e.g., model name, environment)
- `customMetrics`: Dict[str, float] - quantitative data (e.g., token count, latency)
- Both are optional but commonly used for advanced tracking

### Legacy Compatibility
- `olakai_supervisor()` is aliased to `olakai_monitor()` for backward compatibility
- Old v0.3.x API had `init_olakai_client()` with complex options - now simplified
- Migration involved removing `sanitize`, `priority`, `batchSize`, `enableStorage` options

### Testing Considerations
- Tests use `@patch('src.olakaisdk.client.api.send_to_api_simple')` to mock API calls
- No actual network calls in unit tests
- Tests verify decorator doesn't break function behavior or error propagation

## Naming Conventions

- **Functions**: Snake case (e.g., `olakai_config`, `send_to_api`)
- **Classes/Types**: PascalCase (e.g., `OlakaiConfig`, `MonitorPayload`)
- **Private globals**: Leading underscore (e.g., `_global_config`)
- **Constants**: UPPER_SNAKE_CASE (though not many in this codebase)

## Common Patterns

### Adding a New Monitoring Option
1. Add field to `MonitorOptions` in `shared/types.py`
2. Update `OlakaiEventParams` if it's an event parameter
3. Modify `olakai_monitor()` in `core.py` to extract from `options.get()`
4. Update `MonitorPayload` construction to include the field
5. Add test in `tests/test_basic.py`

### Adding a New API Endpoint
1. Add new call_type to `make_api_call()` in `client/api.py`
2. Create corresponding payload type in `shared/types.py`
3. Add response type if different from `APIResponse`
4. Create public function in `core.py` that uses the new endpoint

### Debugging API Calls
- Enable debug mode: `olakai_config("key", "https://endpoint", debug=True)`
- Debug prints show: SDK initialization, API call URLs, status codes, errors
- Check for `RuntimeError` about event loop when using sync functions

## Package Distribution

- Package name: `olakaisdk` (PyPI)
- Version defined in: `pyproject.toml` (version = "0.4.0")
- Source location: `src/olakaisdk/`
- Requires Python 3.7+
- Dependencies: `requests>=2.25.0`, `typing-extensions>=3.7.4` (for Python < 3.8)

## Migration Notes (v0.3.x → v0.4.0)

This was a breaking change that simplified the API:
- Removed batch processing and local storage
- Removed sanitization and priority queuing
- Simplified decorator from `@olakai_supervisor()` to `@olakai_monitor()`
- Replaced `init_olakai_client()` with `olakai_config()`
- Moved to flat parameter structure with `customDimensions` and `customMetrics`
