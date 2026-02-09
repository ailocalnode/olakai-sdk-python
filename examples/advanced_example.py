"""
Advanced example demonstrating real-world use cases with Olakai SDK.

This script shows:
1. Customer support chatbot
2. Content generation with metadata
3. Error handling and retries
4. Nested contexts

Usage:
    export OLAKAI_API_KEY=your-olakai-key
    export OPENAI_API_KEY=your-openai-key
    python examples/advanced_example.py
"""

import asyncio
import os
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from olakaisdk import olakai_config, instrument_openai, olakai_context


def setup():
    """Setup SDK and OpenAI."""
    olakai_api_key = os.getenv("OLAKAI_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not olakai_api_key or not openai_api_key:
        print("❌ Error: Set OLAKAI_API_KEY and OPENAI_API_KEY environment variables")
        sys.exit(1)

    olakai_config(olakai_api_key, debug=True)
    instrument_openai()

    try:
        from openai import OpenAI
        return OpenAI(api_key=openai_api_key)
    except ImportError:
        print("❌ Error: Install OpenAI SDK with: pip install openai")
        sys.exit(1)


def example_customer_support(client):
    """Example: Customer support chatbot with user tracking."""
    print("\n" + "=" * 60)
    print("Example 1: Customer Support Chatbot")
    print("=" * 60 + "\n")

    def handle_support_query(user_email, question, query_type):
        """Handle a customer support query."""

        with olakai_context(
            userEmail=user_email,
            task="Customer Support",
            subTask=query_type,
            customData={
                "channel": "chat",
                "priority": "normal"
            }
        ):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful customer support agent."},
                    {"role": "user", "content": question}
                ],
                max_tokens=150
            )

        return response.choices[0].message.content

    # Simulate different support queries
    queries = [
        ("alice@example.com", "How do I reset my password?", "authentication"),
        ("bob@example.com", "Why was I charged twice?", "billing"),
        ("charlie@example.com", "The app is crashing", "technical-issue")
    ]

    for user_email, question, query_type in queries:
        print(f"User: {user_email}")
        print(f"Query: {question}")

        answer = handle_support_query(user_email, question, query_type)

        print(f"Response: {answer[:150]}...")
        print()


def example_content_generation(client):
    """Example: Content generation with metadata."""
    print("\n" + "=" * 60)
    print("Example 2: Content Generation with Metadata")
    print("=" * 60 + "\n")

    def generate_content(content_type, topic, target_audience):
        """Generate content with tracking."""

        with olakai_context(
            userEmail="content-team@example.com",
            task="Content Generation",
            subTask=content_type,
            customData={
                "content_type": content_type,
                "target_audience": target_audience,
                "topic_category": "technology",
                "target_word_count": 100
            }
        ):
            prompt = f"Write a {content_type} about {topic} for {target_audience} audience. Keep it under 100 words."

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )

        return response.choices[0].message.content

    # Generate different types of content
    content_requests = [
        ("blog-intro", "AI in healthcare", "healthcare professionals"),
        ("social-post", "new AI features", "tech enthusiasts"),
        ("email", "product updates", "existing customers")
    ]

    for content_type, topic, audience in content_requests:
        print(f"Generating {content_type} about '{topic}' for {audience}...")

        content = generate_content(content_type, topic, audience)

        print(f"Result: {content[:200]}...")
        print()


def example_error_handling(client):
    """Example: Error handling with retry logic."""
    print("\n" + "=" * 60)
    print("Example 3: Error Handling and Retries")
    print("=" * 60 + "\n")

    def robust_llm_call(prompt, max_retries=3):
        """Make LLM call with retry logic."""

        for attempt in range(max_retries):
            try:
                with olakai_context(
                    userEmail="system@example.com",
                    task="Robust Call",
                    subTask="retry-example",
                    customData={
                        "attempt": attempt + 1,
                        "retry_count": attempt
                    }
                ):
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=100
                    )

                print(f"✅ Success on attempt {attempt + 1}")
                return response.choices[0].message.content

            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {type(e).__name__}")

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"   Max retries reached, giving up")
                    raise

    # Test robust call
    try:
        result = robust_llm_call("What is the capital of France?")
        print(f"Response: {result}")
    except Exception as e:
        print(f"Final error: {e}")

    print()


def example_nested_contexts(client):
    """Example: Nested contexts for hierarchical tracking."""
    print("\n" + "=" * 60)
    print("Example 4: Nested Contexts")
    print("=" * 60 + "\n")

    # Outer context: User session
    with olakai_context(
        userEmail="demo@example.com",
        task="Multi-Step Workflow",
        customData={"workflow_id": "workflow-123"}
    ):
        print("Step 1: Understanding user intent...")

        # Inner context: Step 1
        with olakai_context(subTask="intent-detection"):
            response1 = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "I want to buy a laptop"}],
                max_tokens=50
            )
            print(f"  Intent: {response1.choices[0].message.content[:100]}")

        print("\nStep 2: Generating recommendations...")

        # Inner context: Step 2
        with olakai_context(subTask="recommendation"):
            response2 = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Recommend 3 laptops for programming"}],
                max_tokens=150
            )
            print(f"  Recommendations: {response2.choices[0].message.content[:150]}...")

        print("\nStep 3: Follow-up question...")

        # Inner context: Step 3
        with olakai_context(subTask="follow-up"):
            response3 = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Which one has the best battery life?"}],
                max_tokens=100
            )
            print(f"  Answer: {response3.choices[0].message.content[:100]}...")

    print("\n✅ Multi-step workflow completed!")
    print("   All steps tracked with proper hierarchy")
    print()


async def main():
    """Run all advanced examples."""

    print("\n" + "=" * 60)
    print("Olakai SDK v0.5.0 - Advanced Examples")
    print("=" * 60)

    # Setup
    client = setup()

    # Run examples
    example_customer_support(client)
    example_content_generation(client)
    example_error_handling(client)
    example_nested_contexts(client)

    # Summary
    print("\n" + "=" * 60)
    print("✅ All advanced examples completed!")
    print("=" * 60)
    print("\n📊 Check your Olakai dashboard at https://app.olakai.ai")
    print("\nWhat you can analyze:")
    print("  - Support query patterns by type")
    print("  - Content generation performance")
    print("  - Error rates and retry patterns")
    print("  - Multi-step workflow tracking")
    print("  - Per-user and per-task analytics\n")


if __name__ == "__main__":
    asyncio.run(main())
