# Olakai SDK

A Python SDK for monitoring function calls and controlling execution with real-time API decisions.

[![PyPI version](https://badge.fury.io/py/olakai-sdk.svg)](https://badge.fury.io/py/olakai-sdk)
[![Python](https://img.shields.io/badge/Python-3.7+-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

## 🎯 **What Does This SDK Do?**

**Olakai SDK supervises your function calls** by wrapping them with intelligent control and monitoring. Perfect for:

- **🛡️ AI/LLM Applications**: Control and monitor AI model calls (OpenAI, Anthropic, etc.)
- **🔒 Sensitive Data Processing**: Prevent unauthorized access to sensitive operations
- **📊 Function Analytics**: Track performance, usage patterns, and errors
- **🚪 Access Control**: Enforce user permissions and content policies
- **⚡ Production Monitoring**: Real-time insights into function behavior

## 🔄 **How It Works: 5-Step Supervision Process**

When you wrap a function with `olakai_supervisor`, every call goes through these steps:

```
1. 🛡️  Control Call (OlakaiAPI) → Check if function should be allowed to run. Failfast: if the the call isn't allowed, it will raise an exception (see below for details)
2. ⚙️  Middleware beforeCall → Pre-processing, validation, transformations
3. 🎯  Function Call → Your actual function executes
4. ⚙️  Middleware afterCall → Post-processing, result transformations
5. 📊  Monitoring (OlakaiAPI) → Log call data, performance metrics, and results
```

**Key Points:**

- **FailFast Control Call** : if the Control Call fails or doesn't allowed the execution of the function, it will raise an Exception (see below for details).
- **FailFast Function Call** : if the original function fails, it will raise the corresponding exception.
- **FailSafe Operations** : if the Middleware or the Monitoring operation fails, it will log and continue the process.

---

## 🚀 **Key Benefits**

### ✅ **Zero Configuration Monitoring**

Just wrap your functions and start monitoring immediately

### ✅ **Smart Type Inference**

TypeScript automatically figures out your function types

### ✅ **Production Ready**

Built-in error handling, retries, and offline support (configurable)

---

## Installation

```bash
pip install olakaisdk
```

## Quick Start - The Easy & Fast Way

```python
from openai import OpenAI
from olakaisdk import init_olakai_client, olakai_supervisor

# 1. Initialize the Olakai client
init_olakai_client("your-olakai-api-key", "https://your-olakai-domain.ai")

#Example for OpenAI API
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

# 2. Wrap any function - that's it!
@olakai_supervisor()
def complete_my_prompt(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4o",  # Specify the model you want to use
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=100,  # Optional: Limit the length of the response
    )

# 3. Use normally - monitoring happens automatically
result = complete_my_prompt("Give me baby name ideas!")
print(result)  # "Hello, World!"
```

**That's it!** Your function calls are now being monitored automatically. No complex configuration needed.

**What it does?** All inputs and outputs of the function are being sent to the API!

**How?** The inputs will be displayed as the "prompt" and the return object as the "response". (in the UNO product)

**What you get:**

- ✅ Every prompt and response is automatically logged to Olakai Platform
- ✅ No changes to your existing code logic

<details>
<summary><strong>Alternative: Monitor just the API call</strong></summary>

```python
import openai
from olakaisdk import init_olakai_client, olakai_supervisor

init_olakai_client("your-olakai-api-key", "https://your-olakai-domain.ai")

openai.api_key = "your-openai-api-key"

# Create a monitored version of the API call
@olakai_supervisor()
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


## Simple Examples

### Monitor Any Function

```python
from olakaisdk import init_olakai_client, olakai_supervisor

init_olakai_client("your-olakai-api-key", "https://your-olakai-domain.ai")

# Works with any function
@olakai_supervisor(
    task="Customer service",     # Optional: give it a task
    subTask="process-order"      # Optional: give it a subtask
)
def process_order(order_id: str) -> dict:
    # Your business logic
    return {"success": True, "order_id": order_id}

result = process_order("order-123")
```

**What it does?** The difference here, is that you can pass additional options, like subtask and task if you want your Olakai's calls to be specific! This helps for analytics generation!

### Track Users (For Multi-User Apps)

```python
from olakaisdk import init_olakai_client, olakai_supervisor

init_olakai_client("your-olakai-api-key", "https://your-olakai-domain.ai")

@olakai_supervisor(
    task="Customer service",
    subTask="process-order",
    email="example@olakai.ai",  # Or use a function: lambda args: get_user_email(args[0])
    chatId="123"                # Or use a function: lambda args: get_session_id(args[0])
)
def process_order(order_id: str) -> dict:
    # Your business logic
    return {"success": True, "order_id": order_id}

result = process_order("order-123")
```

**What it does?** This feature lets you specify a user email, so our API can associate each call with a specific user. Instead of seeing "Anonymous user" in the UNO product's prompts panel, you'll see the actual user linked to each call. For now the matching is based on users' email.


## Common Patterns

### Capture Only What You Need

```python
from olakaisdk import init_olakai_client, olakai_supervisor

init_olakai_client("your-olakai-api-key", "https://your-olakai-domain.ai")

# Custom capture logic
@olakai_supervisor(
    capture=lambda args, result: {
        "input": {"email": args[0]},
        "output": {"success": result.get("success")}
    }
)
def my_function(email: str, password: str) -> dict:
    # This will only capture email, not password
    return {"success": True, "user_id": "123"}
```

---

## When You Need More Control

### Advanced Monitoring

Sometimes you need fine-grained control. Use the full `MonitorOptions` for complete customization:

```python
import time
import requests
from olakaisdk import init_olakai_client, olakai_supervisor

init_olakai_client("your-olakai-api-key", "https://your-olakai-domain.ai")

@olakai_supervisor(
    task="Authentication",
    subTask="user-login",
    email=lambda args: args[0],  # Dynamic user email from first argument
    chatId=lambda args: args[1], # Session tracking from second argument
    sanitize=True,               # Remove sensitive data
    priority="high",             # Queue priority
    capture=lambda args, result: {
        "input": {
            "email": args[0],
            "request_time": int(time.time())
        },
        "output": {
            "success": result.get("success"),
            "user_id": result.get("user_id"),
            "status_code": result.get("status_code")
        }
    }
)
def login_user(email: str, session_id: str, password: str) -> dict:
    """
    Authenticate user against external API
    """
    try:
        # Call external authentication service
        auth_response = requests.post(
            "https://api.auth-service.com/v1/authenticate",
            json={
                "email": email,
                "password": password,
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            return {
                "success": True,
                "user_id": auth_data.get("user_id"),
                "access_token": auth_data.get("access_token"),
                "status_code": 200
            }
        elif auth_response.status_code == 401:
            return {
                "success": False,
                "error": "Invalid credentials",
                "status_code": 401
            }
        else:
            return {
                "success": False,
                "error": f"Authentication service error: {auth_response.status_code}",
                "status_code": auth_response.status_code
            }
            
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}",
            "status_code": 500
        }

result = login_user("user@example.com", "session-123", "secret")
```
Here you choose precisely what field you are sending to Olakai, if you want to be sure not to divulge crucial information. 
In all cases, you should keep in mind not to wrap such sensitive functions to avoid exposing confidential data.

The capture process transforms the function's arguments and return value into input/output data using the provided capture function,
which extracts the relevant information to be sent to Olakai's monitoring API for analysis and tracking.

### Async Support

Works seamlessly with async functions:

```python
import asyncio
from olakaisdk import init_olakai_client, olakai_supervisor

init_olakai_client("your-olakai-api-key", "https://your-olakai-domain.ai")

@olakai_supervisor()
async def async_ai_call(prompt: str) -> str:
    # Your async AI logic
    await asyncio.sleep(0.1)
    return f"Async response to: {prompt}"

# Use with await as normal
result = await async_ai_call("Hello async world!")
```

---

## Configuration

### Basic Setup

```python
from olakaisdk import init_olakai_client

# Simple initialization
client = init_olakai_client("your-olakai-api-key", "https://your-olakai-domain.ai")
```

### Advanced Configuration

```python
from olakaisdk import init_olakai_client

client = init_olakai_client(
    api_key="your-olakai-api-key",
    domain="https://your-olakai-domain.ai",
    debug=True,            # See what's happening
    enableStorage=True,    # Offline support
    batchSize=20,          # Custom batch size
    timeout=30000          # Custom timeout in milliseconds
)
```

### Advanced Debug Mode

```python
from olakaisdk import init_olakai_client

client = init_olakai_client(
    api_key="your-key",
    domain="https://your-olakai-domain.ai",
    debug=True,
    verbose=True
)
```

This will log detailed information about what the SDK is doing.

---

## Tips & Best Practices

### ✅ **Do This**

- Start with `@olakai_supervisor()` decorator
- Use descriptive task names
- Monitor important business logic functions
- Set up user tracking for multi-user apps
- Create one init_olakai_client instance per application

### ❌ **Avoid This**

- Don't monitor every tiny utility function
- Don't put sensitive data in task names
- Don't monitor authentication functions that handle passwords

### 🔒 **Security Notes**

- User emails should match Olakai accounts
- Enable `sanitize=True` for functions handling sensitive data
- Use custom `capture` functions to exclude sensitive parameters

---

## API Reference

### Core Classes and Methods

| Class/Method              | Description                        | Use Case             |
| ------------------------- | ---------------------------------- | -------------------- |
| `init_olakai_client(key, url)`  | Initialize SDK client instance     | Required setup       |
| `client.monitor(options)` | Decorator for monitoring functions | Most common use case |

### Configuration Options (init_olakai_client)

| Option               | Default | Description                |
| -------------------- | ------- | -------------------------- |
| `api_key`            | Required| Your Olakai API key        |
| `domain`             | Default | API endpoint domain        |
| `batchSize`          | `10`    | Requests to batch together |
| `batchTimeout`       | `5000`  | Batch timeout (ms)         |
| `retries`            | `3`     | Retry attempts             |
| `timeout`            | `20000` | Request timeout (ms)       |
| `enableStorage`      | `True`  | Offline queue support      |
| `debug`              | `False` | Debug logging              |
| `verbose`            | `False` | Verbose logging            |

### Monitor Options 

| Option                   | Type                | Description                                                        |
| ------------------------ | ------------------- | ------------------------------------------------------------------ |
| `email`                  | `str` or `Callable` | User email for tracking                                            |
| `chatId`                 | `str` or `Callable` | Chat/session ID                                                    |
| `task`                   | `str`               | Task category                                                      |
| `subTask`                | `str`               | Specific task                                                      |                                            |
| `sanitize`               | `bool`              | Remove sensitive data                                              |
| `priority`               | `str`               | Queue priority (low/normal/high)                                   |
| `capture`                | `Callable`          | Custom data capture function                                       |
| `send_on_function_error` | `bool`              | Enable send to Olakai UNO when the monitored function has an error |


---

## Troubleshooting

### Common Issues

**"Function not being monitored"**

- Check that `init_olakai_client` was instantiated correctly
- Verify your API key and domain URL
- Check console for errors (if debug=True)

**"Import errors"**

- Make sure you installed with `pip install olakaisdk`
- Check Python version (3.7+ required)

**"Monitoring seems slow"**

- Monitoring happens asynchronously and shouldn't affect performance
- Use `priority="low"` for non-critical functions (only affetced when batching is enable)
- Check network connectivity

---

## Examples Repository (not implemented yet)

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
