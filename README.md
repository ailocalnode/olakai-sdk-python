# Olakai SDK

A Python SDK for monitoring function calls and controlling execution with real-time API decisions.

[![PyPI version](https://badge.fury.io/py/olakai-sdk.svg)](https://badge.fury.io/py/olakai-sdk)
[![Python](https://img.shields.io/badge/Python-3.7+-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

## Installation

```bash
pip install olakai-sdk
```

## Quick Start - The Easy & Fast Way

```python
from olakai_sdk import init_client, olakai_monitor

# 1. Initialize once
init_client("your-olakai-api-key", "https://your-olakai-domain.ai")

# 2. Wrap any function - that's it!
@olakai_monitor()
def say_hello(name: str) -> str:
    return f"Hello, {name}!"

# 3. Use normally - monitoring happens automatically
result = say_hello("World")
print(result)  # "Hello, World!"
```

**That's it!** Your function calls are now being monitored automatically. No complex configuration needed.

**What it does?** All inputs and outputs of the function are being sent to the API!

**How?** The inputs will be displayed as the "prompt" and the return object as the "response". (in the UNO product)

<details>
<summary><strong>🤖 Real Example: OpenAI API Call (Click to expand)</strong></summary>

See how easy it is to add monitoring to an existing OpenAI API call:

**Before (without monitoring):**

```python
import openai

openai.api_key = "your-openai-api-key"

def generate_response(prompt: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Usage
response = generate_response("Explain quantum computing")
```

**After (with monitoring):**

```python
import openai
from olakai_sdk import init_client, olakai_monitor

# Initialize Olakai SDK
init_client("your-olakai-api-key", "https://your-olakai-domain.ai")

openai.api_key = "your-openai-api-key"

# Just add the decorator - that's the only change!
@olakai_monitor()
def generate_response(prompt: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Usage (exactly the same)
response = generate_response("Explain quantum computing")
```

**What you get:**

- ✅ Every prompt and response is automatically logged to Olakai
- ✅ Token usage and response times are tracked
- ✅ No changes to your existing code logic
- ✅ If monitoring fails, your function still works perfectly
</details>

<details>
<summary><strong>Alternative: Monitor just the API call</strong></summary>

```python
import openai
from olakai_sdk import init_client, olakai_monitor

init_client("your-olakai-api-key", "https://your-olakai-domain.ai")

openai.api_key = "your-openai-api-key"

# Create a monitored version of the API call
@olakai_monitor()
def monitored_completion(messages: list) -> dict:
    return openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

def generate_response(prompt: str) -> str:
    # Use the monitored API call
    completion = monitored_completion([
        {"role": "user", "content": prompt}
    ])
    return completion.choices[0].message.content
```

_This approach lets you monitor specific API calls while keeping your business logic separate._

</details>

---

## 🚀 **Why Use Olakai SDK?**

### ✅ **Zero Configuration Monitoring**

Just add a decorator and start monitoring immediately

### ✅ **Never Breaks Your Code**

If monitoring fails, your functions still work perfectly

### ✅ **Smart Type Support**

Works seamlessly with Python type hints

### ✅ **Production Ready**

Built-in error handling, retries, and offline support

---

## Simple Examples

### Monitor Any Function

```python
from olakai_sdk import olakai_monitor
from olakai_sdk.types import MonitorOptions

# Works with any function
@olakai_monitor(MonitorOptions(
    task="Customer service",     # Optional: give it a task
    subTask="process-order"      # Optional: give it a subtask
))
def process_order(order_id: str) -> dict:
    # Your business logic
    return {"success": True, "order_id": order_id}

result = process_order("order-123")
```

**What it does?** The difference here, is that you can pass additional options, like subtask and task if you want your Olakai's calls to be specific! This helps for analytics generation!

### Track Users (For Multi-User Apps)

```python
from olakai_sdk import olakai_monitor
from olakai_sdk.types import MonitorOptions

@olakai_monitor(MonitorOptions(
    task="Customer service",
    subTask="process-order",
    email="example@olakai.ai",  # Or use a function: lambda args: get_user_email(args[0])
    chatId="123"                # Or use a function: lambda args: get_session_id(args[0])
))
def process_order(order_id: str) -> dict:
    # Your business logic
    return {"success": True, "order_id": order_id}

result = process_order("order-123")
```

**What it does?** This feature lets you specify a user email, so our API can associate each call with a specific user. Instead of seeing "Anonymous user" in the UNO product's prompts panel, you'll see the actual user linked to each call. For now the matching is based on users' email.

### Obtain Scoring of the Prompt

```python
from olakai_sdk import olakai_monitor
from olakai_sdk.types import MonitorOptions

@olakai_monitor(MonitorOptions(
    task="Customer service",
    subTask="process-order",
    email="example@olakai.ai",
    chatId="123",
    shouldScore=True  # Enable prompt scoring
))
def process_order(order_id: str) -> dict:
    # Your business logic
    return {"success": True, "order_id": order_id}

result = process_order("order-123")
```

**What it does?** This feature lets you specify if the "prompt" (so the args of the function you monitor), should get a "prompting score", the same way Olakai is doing it for standard prompts in the UNO product.

## Common Patterns

### Capture Only What You Need

```python
from olakai_sdk import olakai_monitor
from olakai_sdk.types import MonitorOptions

# Custom capture logic
@olakai_monitor(MonitorOptions(
    capture=lambda args, result: {
        "input": {"email": args[0]},
        "output": {"success": result.get("success")}
    }
))
def my_function(email: str, password: str) -> dict:
    # This will only capture email, not password
    return {"success": True, "user_id": "123"}
```

### Error Handling Made Easy

```python
from olakai_sdk import olakai_monitor
from olakai_sdk.types import MonitorOptions

@olakai_monitor(MonitorOptions(
    task="risky-operation",
    on_error=lambda error, args: {
        "input": args[0],
        "output": {"error": str(error)}
    }
))
def risky_operation(data: dict) -> dict:
    # This might raise an exception
    if not data.get("valid"):
        raise ValueError("Invalid data")
    return {"success": True}
```

---

## When You Need More Control

### Advanced Monitoring

Sometimes you need fine-grained control. Use the full `MonitorOptions` for complete customization:

```python
from olakai_sdk import olakai_monitor
from olakai_sdk.types import MonitorOptions

@olakai_monitor(MonitorOptions(
    task="Authentication",
    subTask="user-login",
    email=lambda args: args[0],  # Dynamic user email from first argument
    chatId=lambda args: args[1], # Session tracking from second argument
    shouldScore=True,
    sanitize=True,               # Remove sensitive data
    priority="high",             # Queue priority
    capture=lambda args, result: {
        "input": {
            "email": args[0],
            "request_time": int(time.time())
        },
        "output": {
            "success": result.get("success"),
            "user_id": result.get("user_id")
        }
    }
))
def login_user(email: str, session_id: str, password: str) -> dict:
    # Your login logic (password won't be captured due to custom capture)
    return {"success": True, "user_id": "123"}

result = login_user("user@example.com", "session-123", "secret")
```

### Async Support

Works seamlessly with async functions:

```python
import asyncio
from olakai_sdk import olakai_monitor

@olakai_monitor()
async def async_ai_call(prompt: str) -> str:
    # Your async AI logic
    await asyncio.sleep(0.1)
    return f"Async response to: {prompt}"

# Use with await as normal
result = await async_ai_call("Hello async world!")
```

---

## Configuration

### Setup

```python
from olakai_sdk import init_client

init_client("your-olakai-api-key", "https://your-olakai-domain.ai")
```

### Advanced Configuration

```python
from olakai_sdk import init_client
from olakai_sdk.types import SDKConfig

init_client(SDKConfig(
    apiKey="your-olakai-api-key",
    apiUrl="https://your-olakai-domain.ai",
    debug=True,          # See what's happening
    enableLocalStorage=True  # Offline support
))
```

### Advanced Debug Mode

```python
from olakai_sdk import init_client
from olakai_sdk.types import SDKConfig

init_client(SDKConfig(
    apiKey="your-key",
    apiUrl="https://your-olakai-domain.ai",
    debug=True,
    verbose=True
))
```

This will log detailed information about what the SDK is doing.

---

## Tips & Best Practices

### ✅ **Do This**

- Start with simple `@monitor()` decorator
- Use descriptive task names
- Monitor important business logic functions
- Set up user tracking for multi-user apps

### ❌ **Avoid This**

- Don't monitor every tiny utility function
- Don't put sensitive data in task names
- Don't monitor authentication functions that handle passwords

### 🔒 **Security Notes**

- The SDK automatically sanitizes common sensitive patterns
- User emails should match Olakai accounts
- Enable `sanitize=True` for functions handling sensitive data
- Use custom `capture` functions to exclude sensitive parameters

---

## API Reference

### Core Functions

| Function                | Description                        | Use Case             |
| ----------------------- | ---------------------------------- | -------------------- |
| `init_client(key, url)` | Initialize SDK with API key        | Required setup       |
| `@monitor(options?)`    | Decorator for monitoring functions | Most common use case |

### Configuration Options (SDKConfig)

| Option               | Default | Description                |
| -------------------- | ------- | -------------------------- |
| `apiKey`             | `""`    | Your Olakai API key        |
| `apiUrl`             | `None`  | API endpoint URL           |
| `batchSize`          | `10`    | Requests to batch together |
| `batchTimeout`       | `5000`  | Batch timeout (ms)         |
| `retries`            | `3`     | Retry attempts             |
| `timeout`            | `20000` | Request timeout (ms)       |
| `enableLocalStorage` | `True`  | Offline queue support      |
| `debug`              | `False` | Debug logging              |
| `verbose`            | `False` | Verbose logging            |

### Monitor Options (MonitorOptions)

| Option        | Type                | Description                      |
| ------------- | ------------------- | -------------------------------- |
| `email`       | `str` or `Callable` | User email for tracking          |
| `chatId`      | `str` or `Callable` | Chat/session ID                  |
| `task`        | `str`               | Task category                    |
| `subTask`     | `str`               | Specific task                    |
| `shouldScore` | `bool`              | Enable prompt scoring            |
| `sanitize`    | `bool`              | Remove sensitive data            |
| `priority`    | `str`               | Queue priority (low/normal/high) |
| `capture`     | `Callable`          | Custom data capture function     |
| `on_error`    | `Callable`          | Error handling function          |

### Utilities

- `get_config()` - Get current SDK configuration
- `get_queue_size()` - Check request queue size
- `clear_queue()` - Clear pending requests
- `flush_queue()` - Send all queued requests immediately

---

## Troubleshooting

### Common Issues

**"Function not being monitored"**

- Check that `init_client()` was called first
- Verify your API key and domain URL
- Check console for errors (if debug=True)

**"Import errors"**

- Make sure you installed with `pip install olakai-sdk`
- Check Python version (3.7+ required)

**"Monitoring seems slow"**

- Monitoring happens asynchronously and shouldn't affect performance
- Use `priority="low"` for non-critical functions
- Check network connectivity

---

## Examples Repository

Check out our [examples repository](https://github.com/olakai/sdk-examples-python) for complete working examples:

- Flask REST API
- Django application
- Database monitoring
- Authentication flows
- Error handling patterns

---

## License

MIT © [Olakai](https://olakai.ai)

---

**Need help?**

- 📖 [Documentation](https://app.olakai.ai/docs/getting-started/getting-started)
- 📧 [Support Email](mailto:support@olakai.ai)
