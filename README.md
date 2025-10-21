# Olakai Python SDK

**The simplest way to monitor your AI/ML applications** - Track every prompt, response, and interaction with just one line of code.

[![PyPI version](https://badge.fury.io/py/olakai-sdk.svg)](https://badge.fury.io/py/olakai-sdk)
[![Python](https://img.shields.io/badge/Python-3.7+-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

---

## What This Does

Transform any Python function into a monitored AI interaction with **zero configuration**. Perfect for:

- **AI/LLM Applications** - Monitor OpenAI, Anthropic, or any AI model calls
- **Analytics & Insights** - Track usage patterns, performance, and user behavior
- **Content Safety** - Detect and block inappropriate content automatically
- **User Management** - Track individual users and their AI interactions
- **Business Intelligence** - Understand how your AI features are being used

---

## Quick Start (30 seconds)

```python
from olakaisdk import olakai_config, olakai_monitor

# 1. Initialize (one time setup)
olakai_config("your-api-key", "https://your-domain.ai")

# 2. Wrap any function (that's it!)
@olakai_monitor()
def my_ai_function(prompt: str):
    # Your AI logic here
    return f"AI response to: {prompt}"

# 3. Use normally - monitoring happens automatically
result = my_ai_function("Hello world!")
```

**That's it!** Your function is now being monitored. Check your [Olakai dashboard](https://app.olakai.ai) to see the data.

---

## Installation

```bash
pip install olakaisdk
```

**Requirements:** Python 3.7+ and `requests` library (installed automatically)

---

## Real-World Examples

### OpenAI Integration

```python
from olakaisdk import olakai_config, olakai_monitor
from openai import OpenAI

# Setup
olakai_config("your-olakai-key", "https://your-domain.ai")
client = OpenAI(api_key="your-openai-key")

# Monitor your AI calls
@olakai_monitor(
    userEmail="user@example.com",
    task="Customer Support",
    customDimensions={"dim1": "gpt-4", "dim2": "support"},
    customMetrics={"metric1": 150, "metric2": 2.3}
)
def get_ai_response(user_question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_question}],
        max_tokens=200
    )
    return response.choices[0].message.content

# Use it!
answer = get_ai_response("How do I reset my password?")
```

### E-commerce AI Assistant

```python
@olakai_monitor(
    userEmail=lambda args: get_user_email(args[0]),  # Dynamic user email
    chatId=lambda args: get_session_id(args[0]),  # Dynamic session
    task="Customer Experience",
    subTask="customer service",
    customDimensions={"dim1": "premium", "dim2": "fashion"},
    customMetrics={"metric1": 5, "metric2": 0.23}
)
def recommend_products(user_id: str, preferences: dict) -> list:
    # Your recommendation logic
    return ["Product A", "Product B", "Product C"]
```

### Email AI Writer

```python
@olakai_monitor(
    task="Communication Strategy",
    subTask="communication/persuasion",
    customDimensions={"dim1": "promotional", "dim2": "existing_customers"},
    customMetrics={"metric1": 250, "metric2": 0.8}
)
def generate_email_campaign(topic: str, tone: str) -> str:
    # Your email generation logic
    return f"Subject: {topic}\n\nDear Customer, ..."
```

---

## Advanced Features

### Custom Dimensions & Metrics

Track any data you want alongside your AI interactions:

```python
@olakai_monitor(
    # String dimensions (categorical data)
    customDimensions={"dim1": "gpt-4", "dim2": "production", "dim3": "premium", "dim4": "en"},
    # Numeric metrics (quantitative data)
    customMetrics={"metric1": 150, "metric2": 2.5, "metric3": 0.95, "metric4": 0.02}
)
def advanced_ai_function(prompt: str) -> str:
    return "AI response"
```

### User Tracking

Track individual users and their AI interactions:

```python
@olakai_monitor(
    userEmail="john.doe@company.com",  # User email
    chatId="session-abc123",       # Session/conversation ID
    task="Personal Productivity",
    subTask="email management"
)
def personal_assistant(user_request: str) -> str:
    return "Assistant response"
```

### Direct Reporting

Report events manually without decorators:

```python
from olakaisdk import olakai_report

olakai_report(
    prompt="User asked about pricing",
    response="Here are our pricing plans...",
    options={
        "userEmail": "user@example.com",
        "chatId": "pricing-session-123",
        "task": "Sales Support",
        "customDimensions": {"dim1": "pricing"},
        "customMetrics": {"metric1": 1.2}
    }
)
```

### Low-Level Event Tracking

For maximum control:

```python
from olakaisdk import olakai, OlakaiEventParams

params = OlakaiEventParams(
    prompt="Custom prompt",
    response="Custom response",
    userEmail="user@example.com",
    chatId="custom-session",
    task="Custom Task",
    customDimensions={"dim1": "lowlevel"},
    customMetrics={"metric1": 0.85},
    shouldScore=True,
    tokens=100,
    requestTime=500
)

olakai("ai_activity", "custom_event", params)
```

---

## Configuration Options

### Basic Setup

```python
from olakaisdk import olakai_config

# Simple setup
olakai_config("your-api-key")

# With custom endpoint
olakai_config("your-api-key", "https://your-domain.ai")

# With debug logging
olakai_config("your-api-key", "https://your-domain.ai", debug=True)
```

### Monitor Options

| Option             | Type   | Description             | Example              |
| ------------------ | ------ | ----------------------- | -------------------- |
| `userEmail`        | `str`  | User email for tracking | `"user@example.com"` |
| `chatId`           | `str`  | Session/conversation ID | `"session-123"`      |
| `task`             | `str`  | Task category           | `"Customer Support"` |
| `subTask`          | `str`  | Specific task           | `"password-reset"`   |
| `customDimensions` | `dict` | String metadata         | `{"dim1": "gpt-4"}`  |
| `customMetrics`    | `dict` | Numeric data            | `{"metric1": 150}`   |
| `shouldScore`      | `bool` | Enable content scoring  | `True`               |

---

## Migration from v0.3.x

**This is a breaking change** - the SDK has been completely simplified!

### Old Way (v0.3.x)

```python
from olakaisdk import init_olakai_client, olakai_supervisor

# Complex setup
init_olakai_client("api-key", "domain", debug=True, batchSize=10, enableStorage=True)

# Complex decorator
@olakai_supervisor(
    sanitize=True,
    priority="high",
    send_on_function_error=True
)
def old_function():
    pass
```

### New Way (v0.4.0)

```python
from olakaisdk import olakai_config, olakai_monitor

# Simple setup
olakai_config("api-key", "https://domain.ai", debug=True)

# Simple decorator
@olakai_monitor(
    userEmail="user@example.com",
    customDimensions={"dim1": "production"}
)
def new_function():
    pass
```

### Migration Steps

1. **Replace initialization:**

   - `init_olakai_client()` → `olakai_config()`

2. **Replace decorator:**

   - `@olakai_supervisor()` → `@olakai_monitor()`

3. **Update parameters:**

   - Use `customDimensions={"dim1": "...", "dim2": "..."}` for string data
   - Use `customMetrics={"metric1": 1.0, "metric2": 2.0}` for numeric data
   - Add `userEmail` and `chatId` for user tracking

4. **Remove complex options:**
   - No more `sanitize`, `priority`, `batchSize`, etc.

---

## Troubleshooting

### Common Issues

**"SDK not initialized"**

```python
# Wrong - using functions before setup
from olakaisdk import olakai_monitor
@olakai_monitor()  # This will fail
def my_function():
    pass

# Correct - setup first
from olakaisdk import olakai_config, olakai_monitor
olakai_config("your-api-key")  # Setup first
@olakai_monitor()  # Now this works
def my_function():
    pass
```

**"Import errors"**

```bash
# Make sure you have the right version
pip install --upgrade olakaisdk

# Check Python version (3.7+ required)
python --version
```

**"API calls not working"**

```python
# Enable debug mode to see what's happening
olakai_config("your-api-key", debug=True)

# Check your API key and endpoint
olakai_config("your-api-key", "https://your-domain.ai", debug=True)
```

**"Monitoring seems slow"**

- Monitoring happens asynchronously and won't slow down your app
- API calls are made in the background
- Check your network connection if issues persist

### Debug Mode

Enable debug mode to see what's happening:

```python
olakai_config("your-api-key", debug=True)

# You'll see output like:
# Olakai SDK initialized with endpoint: https://your-domain.ai
# API call to https://your-domain.ai/api/monitoring/prompt: 200
# API call successful
```

---

## Best Practices

### Do This

- **Start simple:** Begin with `@olakai_monitor()` and add options as needed
- **Use descriptive tasks:** `task="Customer Support"` instead of `task="cs"`
- **Track users:** Always include `userEmail` for user-specific analytics
- **Use custom dimensions:** Track model, environment, user type, etc. with `customDimensions={"dim1": "...", "dim2": "..."}`
- **Use custom metrics:** Track tokens, response time, costs, etc. with `customMetrics={"metric1": 1.0, "metric2": 2.0}`
- **Group related calls:** Use consistent `task` and `subTask` names

### Avoid This

- **Don't monitor everything:** Only monitor important AI interactions
- **Don't put sensitive data in task names:** Use `custom_dimensions` instead
- **Don't monitor auth functions:** Avoid monitoring password/API key handling
- **Don't use the old API:** It's deprecated and will be removed

### Security Tips

- **User emails should match Olakai accounts** for proper user tracking
- **Use custom dimensions** to exclude sensitive parameters with `customDimensions={"dim1": "...", "dim2": "..."}`
- **Never log passwords or API keys** in prompts/responses
- **Consider data privacy** when tracking user interactions

---

## Use Cases

### Enterprise Applications

```python
@olakai_monitor(
    userEmail=lambda args: get_user_email(args[0]),
    task="Enterprise AI",
    subTask="document-analysis",
    customDimensions={"dim1": "acme-corp", "dim2": "legal", "dim3": "contract"},
    customMetrics={"metric1": 10, "metric2": 0.92}
)
def analyze_document(user_id: str, document: str) -> dict:
    # Document analysis logic
    return {"summary": "...", "key_points": [...]}
```

### Educational Platforms

```python
@olakai_monitor(
    userEmail="student@university.edu",
    task="Educational AI",
    subTask="homework-help",
    customDimensions={"dim1": "computer-science", "dim2": "intermediate", "dim3": "algorithms"},
    customMetrics={"metric1": 3, "metric2": 15.5}
)
def help_with_homework(question: str, student_level: str) -> str:
    # Educational AI logic
    return "Here's how to solve this problem..."
```

### Healthcare Applications

```python
@olakai_monitor(
    userEmail="doctor@hospital.com",
    task="Medical AI",
    subTask="symptom-analysis",
    customDimensions={"dim1": "cardiology", "dim2": "adult", "dim3": "routine"},
    customMetrics={"metric1": 5, "metric2": 0.88}
)
def analyze_symptoms(symptoms: list, patient_info: dict) -> dict:
    # Medical AI logic (with proper compliance)
    return {"possible_conditions": [...], "recommendations": [...]}
```

---

## Dashboard & Analytics

After setting up monitoring, visit your [Olakai dashboard](https://app.olakai.ai) to see:

- **Usage Analytics** - Track API calls, users, and trends
- **User Insights** - See individual user behavior and patterns
- **Task Performance** - Monitor different tasks and their success rates
- **Custom Metrics** - View your custom dimensions and metrics
- **Content Safety** - Review flagged content and safety scores
- **Cost Tracking** - Monitor AI usage costs and optimization opportunities

---

## Support & Community

- **Documentation:** [Olakai Docs](https://app.olakai.ai/docs)
- **Support:** [support@olakai.ai](mailto:support@olakai.ai)
- **Issues:** [GitHub Issues](https://github.com/olakai/sdk-python/issues)
- **Examples:** [SDK Examples](https://github.com/olakai/sdk-examples-python)

---

## License

MIT © [Olakai](https://olakai.ai)

---

**Ready to get started?**

```python
from olakaisdk import olakai_config, olakai_monitor

olakai_config("your-api-key")
@olakai_monitor()
def my_first_monitored_function():
    return "Hello, monitored world!"
```

**Happy monitoring!**
