# Changelog

All notable changes to the Olakai Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-04-07

### Added

- `olakai_feedback()` - New function for reporting explicit user feedback
  (thumbs up/down) on a prior agent interaction. Fire-and-forget, never
  raises. Wraps the existing monitoring pipeline with a well-known
  `eventType="feedback"` convention in `customData`, so no server
  changes are required.

## [1.0.0] - 2025-01-07

### 🎉 First Stable Release

This release marks the first stable version of the Olakai Python SDK, signaling production readiness for auto-instrumentation of LLM providers.

### Changed

- Version bump to 1.0.0 for production stability
- **Breaking**: Replaced `customDimensions` and `customMetrics` with unified `customData` field for simpler payload structure
- **Breaking**: Remove chatId from `OlakaiEventParams`; chat/session information is now managed internally

### Added

- `olakai_event()` - New function for manually sending event reports

### Stability

The v1.0.0 API is now stable. The primary API consists of:

- `olakai_config()` - Initialize the SDK
- `instrument_openai()` - Auto-instrument OpenAI SDK
- `olakai_context()` - Add metadata to tracked calls
- `uninstrument_openai()` - Remove instrumentation
- `is_instrumented()` - Check instrumentation status
- `olakai_event()` - Send event report manually

---

## [0.6.0] - 2024-12-30

### Added

- **`userId` field** - Added `userId` parameter to `olakai_context()` for explicit user tracking
- **`userId` in types** - Added `userId` to `OlakaiContextData`, `OlakaiEventParams`, `MonitorOptions`, and `MonitorPayload`

### Changed

- Updated `OlakaiContextData.merge()` to include `userId` in context merging
- Updated `OlakaiContextData.to_dict()` to include `userId` in payload output
- Type definitions now align with backend monitoring API expectations

### Compatibility

- Backwards compatible with existing code
- New `userId` field is optional (defaults to `None`)

## [0.5.0] - 2024-11-19

### 🎉 Major Release: Auto-Instrumentation

This is a major refactor introducing automatic instrumentation for LLM providers. The SDK now focuses on server-side Python applications with zero-configuration monitoring.

### Added

- **Auto-instrumentation for OpenAI** - One-line setup with `instrument_openai()`
- **Context-based metadata** - `olakai_context()` for adding user/session metadata
- **Streaming support** - Automatic handling of OpenAI streaming responses
- **Automatic data extraction** - Tokens, model names, API keys, latency
- **Thread-safe context management** - Using Python's contextvars
- **Privacy controls** - Configure what data to capture (inputs, outputs, API keys)
- **Comprehensive documentation** - New README, USAGE.md, and examples
- **Sample scripts** - basic_example.py and advanced_example.py

### Changed

- **Breaking**: Complete API redesign focused on auto-instrumentation
- **Breaking**: Version bumped to 0.5.0 (not backward compatible with 0.4.x)
- **Simplified**: Removed batching and local storage (server-focused)
- **Improved**: Better error handling and debugging
- **Enhanced**: Richer telemetry with automatic LLM-specific data

### Deprecated

- `@olakai_monitor()` decorator - Use `instrument_openai()` instead
- `olakai_report()` - Use auto-instrumentation instead
- `olakai()` low-level API - Use auto-instrumentation instead

These will be removed in v1.0.0.

### Migration Guide

**Old way (v0.4.0):**

```python
from olakaisdk import olakai_config, olakai_monitor

olakai_config("api-key")

@olakai_monitor(userEmail="user@example.com", task="Support")
def get_response(prompt):
    # Your OpenAI call
    pass
```

**New way (v0.5.0):**

```python
from olakaisdk import olakai_config, instrument_openai, olakai_context

olakai_config("api-key")
instrument_openai()  # One-time setup

# No decorator needed!
with olakai_context(userEmail="user@example.com", task="Support"):
    # Your OpenAI calls are automatically tracked
    pass
```

### Technical Details

**New Architecture:**

- `config.py` - Global configuration management
- `context.py` - Thread-safe context manager using contextvars
- `instrumentation/` - Provider-specific instrumentation (OpenAI)
- `extractors/` - Data extraction from LLM responses

**Test Coverage:**

- 35+ passing tests
- Config tests
- Context tests
- Instrumentation tests
- Extractor tests

### What's Next

Planned for future releases:

- Anthropic (Claude) instrumentation
- Google AI (Gemini) instrumentation
- Local model support (Ollama, LM Studio)
- Enhanced streaming analytics
- Cost optimization recommendations

---

## [0.4.0] - 2024-10-24

### Changed

- Simplified API with `olakai_config()` and `@olakai_monitor()`
- Removed complex initialization options
- Removed batching and priority queuing
- Introduced `customDimensions` and `customMetrics`

### Removed

- `init_olakai_client()` - replaced with `olakai_config()`
- `sanitize` option
- `priority` option
- `batchSize` option
- `enableStorage` option

---

## [0.3.x] - 2024-10-20

### Features

- Initial release with `@olakai_supervisor()` decorator
- Batch processing
- Local storage
- Priority queuing
- Complex configuration

---

## Release Notes

### v0.5.0 Highlights

This release transforms the Olakai SDK into an automatic instrumentation library specifically designed for server-side LLM monitoring. Key improvements:

1. **Zero-friction DX**: Just call `instrument_openai()` once and forget about it
2. **Richer telemetry**: Automatic capture of tokens, costs, models, API keys
3. **Better ergonomics**: Context managers instead of decorators
4. **Server-focused**: Removed client-side features like batching
5. **Extensible**: Clean architecture for adding more LLM providers

### Breaking Changes

v0.5.0 is **not backward compatible** with v0.4.0. The API has been completely redesigned. Please refer to the migration guide above.

### Support

- Documentation: [README.md](./README.md)
- Usage Guide: [USAGE.md](./USAGE.md)
- Examples: [examples/](./examples/)
- Issues: [GitHub Issues](https://github.com/olakai/sdk-python/issues)
- Email: [support@olakai.ai](mailto:support@olakai.ai)
