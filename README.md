# Olakai SDK

A Python SDK for monitoring and tracking external AI/ML model interactions. Enable reporting and control through the Olakai UNO product.

## Features

- 🚀 **Easy Integration**: Simple decorators and function calls to monitor your AI models
- 📊 **Batch Processing**: Efficient batching system for high-throughput applications
- 🔄 **Retry Logic**: Built-in retry mechanism with exponential backoff
- 💾 **Local Storage**: Persistent queue storage for offline scenarios
- 🎯 **Flexible Configuration**: Extensive configuration options for different use cases
- 🔧 **Middleware Support**: Extensible middleware system for custom processing
- ⚡ **Async Support**: Full support for both sync and async functions

## Installation

```bash
pip install olakai-sdk
```

## Quick Start

### 1. Initialize the SDK

```python
from olakai-sdk import init_client

# Initialize with API key
init_client("your-api-key-here", domain="your-domain-url-here")

# Or with custom configuration
from olakai-sdk.types import SDKConfig

config = SDKConfig(
    apiKey="your-api-key-here",
    batchSize=20,
    timeout=30000,
    debug=True
)
init_client(config)
```

### 2. Monitor Function Calls

```python
from olakai-sdk import monitor

@monitor()
def generate_response(prompt: str) -> str:
    # Your AI model logic here
    response = "Generated response"
    return response

# Use the function normally
result = generate_response("Hello, world!")
```

### 3. Manual Monitoring

```python
from olakai-sdk import send_to_api
from olakai-sdk.types import MonitorPayload

payload = MonitorPayload(
    userId="user123",
    chatId="chat456",
    prompt="What is the weather like?",
    response="It's sunny today!",
    tokens=50,
    requestTime=1234567890
)

send_to_api(payload)
```

## Configuration

### SDKConfig Options

| Option                | Type       | Default        | Description                                  |
| --------------------- | ---------- | -------------- | -------------------------------------------- |
| `apiKey`              | `str`      | `""`           | Your Olakai API key                          |
| `apiUrl`              | `str`      | Auto-generated | API endpoint URL                             |
| `batchSize`           | `int`      | `10`           | Number of requests to batch together         |
| `batchTimeout`        | `int`      | `5000`         | Timeout in milliseconds for batch processing |
| `retries`             | `int`      | `3`            | Number of retry attempts for failed requests |
| `timeout`             | `int`      | `20000`        | Request timeout in milliseconds              |
| `enableLocalStorage`  | `bool`     | `True`         | Enable persistent queue storage              |
| `maxLocalStorageSize` | `int`      | `1000000`      | Maximum size of local storage in bytes       |
| `debug`               | `bool`     | `False`        | Enable debug logging                         |
| `verbose`             | `bool`     | `False`        | Enable verbose logging                       |
| `onError`             | `Callable` | `None`         | Error callback function                      |

### Monitor Options

```python
from olakai-sdk.types import MonitorOptions

@monitor(MonitorOptions(
    enabled=True,
    sample_rate=0.1,  # Monitor 10% of calls
    priority="high",
    sanitize=True
))
def my_function():
    pass
```

## Advanced Usage

### Middleware

Add custom processing logic with middleware:

```python
from olakai-sdk import add_middleware
from olakai-sdk.types import Middleware

def before_call(args, kwargs):
    print(f"Function called with args: {args}")

def after_call(result, args, kwargs):
    print(f"Function returned: {result}")

middleware = Middleware(
    name="logger",
    before_call=before_call,
    after_call=after_call
)

add_middleware(middleware)
```

### Async Support

```python
import asyncio
from olakai-sdk import monitor

@monitor()
async def async_generate_response(prompt: str) -> str:
    # Your async AI model logic here
    await asyncio.sleep(0.1)
    return "Async response"

# Use with asyncio
result = await async_generate_response("Hello, async world!")
```

### Queue Management

```python
from olakai-sdk import get_queue_size, flush_queue, clear_queue

# Check queue size
size = get_queue_size()
print(f"Queue size: {size}")

# Force process queue immediately
flush_queue()

# Clear all queued items
clear_queue()
```

### Error Handling

```python
from olakai-sdk.types import SDKConfig

def error_handler(error: Exception):
    print(f"SDK Error: {error}")
    # Send to your logging system

config = SDKConfig(
    apiKey="your-key",
    onError=error_handler
)
```

## API Reference

### Core Functions

- `init_client(key_or_config)` - Initialize the SDK
- `monitor(options=None)` - Decorator for monitoring functions
- `send_to_api(payload, options=None)` - Send data manually
- `get_config()` - Get current configuration
- `get_queue_size()` - Get current queue size
- `flush_queue()` - Process queue immediately
- `clear_queue()` - Clear all queued items

### Middleware Functions

- `add_middleware(middleware)` - Add middleware
- `remove_middleware(name)` - Remove middleware by name

## Examples

### Basic Chat Bot Monitoring

```python
from olakai-sdk import init_client, monitor
from olakai-sdk.types import MonitorOptions

init_client("your-api-key")

@monitor(MonitorOptions(priority="high"))
def chat_completion(user_id: str, message: str) -> str:
    # Your chat completion logic
    response = f"Response to: {message}"
    return response

# Usage
response = chat_completion("user123", "Hello!")
```

### Batch Processing Example

```python
from olakai-sdk import init_client
from olakai-sdk.types import SDKConfig

# Configure for high-throughput
config = SDKConfig(
    apiKey="your-key",
    batchSize=50,
    batchTimeout=1000,  # 1 second
    enableLocalStorage=True
)

init_client(config)
```

## Development

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/olakai-sdk
cd olakai-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=olakai-sdk

# Run specific test file (not implemented yet)
pytest tests/test_client.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: support@olakai.ai
- 📖 Documentation: https://docs.olakai.ai
- 🐛 Issues: https://github.com/your-org/olakai-sdk/issues

## Changelog

### v0.1.0

- Initial release
- Basic monitoring functionality
- Batch processing support
- Local storage persistence
- Middleware system
- Async support
