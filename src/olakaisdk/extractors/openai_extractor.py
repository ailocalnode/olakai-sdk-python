"""Extract telemetry data from OpenAI API responses."""

from typing import Any, Dict, Optional
from ..shared.types import MonitorPayload
from ..context import OlakaiContextData
from .base_extractor import BaseExtractor


class OpenAIExtractor(BaseExtractor):
    """Extract telemetry data from OpenAI API calls."""

    def extract(
        self,
        request_kwargs: Dict[str, Any],
        response: Any,
        client_instance: Any,
        duration_ms: int,
        context: Optional[OlakaiContextData] = None
    ) -> MonitorPayload:
        """
        Extract telemetry data from OpenAI request/response.

        Args:
            request_kwargs: Arguments passed to create()
            response: OpenAI response object
            client_instance: OpenAI client instance
            duration_ms: Request duration in milliseconds
            context: Current Olakai context

        Returns:
            MonitorPayload ready to send
        """
        # Extract from request
        model = request_kwargs.get("model", "unknown")
        messages = request_kwargs.get("messages", [])

        # Extract from response
        tokens_input = 0
        tokens_output = 0
        tokens_total = 0

        if hasattr(response, "usage") and response.usage:
            tokens_input = getattr(response.usage, "prompt_tokens", 0)
            tokens_output = getattr(response.usage, "completion_tokens", 0)
            tokens_total = getattr(response.usage, "total_tokens", 0)

        # Extract text content
        prompt_text = self._extract_prompt(messages) if self.capture_inputs else "[redacted]"
        response_text = self._extract_response(response) if self.capture_outputs else "[redacted]"

        # Extract API key (full key for backend cost tracking)
        api_key_value = None
        if self.capture_api_keys and hasattr(client_instance, "api_key"):
            api_key_value = client_instance.api_key

        # Get context data or use defaults
        context_data = context or OlakaiContextData()

        # Build custom dimensions (merge with context)
        custom_dimensions = dict(context_data.customDimensions or {})
        custom_dimensions.update({
            "model": model,
            "provider": "openai",
            "tokens_input": str(tokens_input),
            "tokens_output": str(tokens_output),
        })

        # Add API key if captured
        if api_key_value:
            custom_dimensions["api_key"] = api_key_value

        # Build custom metrics (merge with context)
        custom_metrics = dict(context_data.customMetrics or {})
        custom_metrics.update({
            "tokens_input": float(tokens_input),
            "tokens_output": float(tokens_output),
            "tokens_total": float(tokens_total),
        })

        # Build payload
        payload = MonitorPayload(
            userEmail=context_data.userEmail or "anonymous@olakai.ai",
            chatId=context_data.chatId or "anonymous",
            prompt=prompt_text,
            response=response_text,
            tokens=tokens_total,
            requestTime=duration_ms,
            task=context_data.task,
            subTask=context_data.subTask,
            customDimensions=custom_dimensions,
            customMetrics=custom_metrics,
            shouldScore=True
        )

        return payload

    def _extract_prompt(self, messages: list) -> str:
        """
        Extract prompt text from messages array.

        Args:
            messages: List of message dictionaries

        Returns:
            Extracted prompt text
        """
        if not messages:
            return ""

        # Get last user message
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    return content
                # Handle complex content (e.g., with images)
                elif isinstance(content, list):
                    text_parts = [
                        part.get("text", "")
                        for part in content
                        if isinstance(part, dict) and part.get("type") == "text"
                    ]
                    return " ".join(text_parts)

        # Fallback: return all messages as string
        return str(messages)

    def _extract_response(self, response: Any) -> str:
        """
        Extract response text from OpenAI response object.

        Args:
            response: OpenAI response object

        Returns:
            Extracted response text
        """
        try:
            if hasattr(response, "choices") and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    content = choice.message.content
                    if content:
                        return content
        except Exception:
            pass

        # Fallback: return string representation
        return str(response)
