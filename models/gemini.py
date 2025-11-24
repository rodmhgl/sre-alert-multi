from typing import Any, Dict

from .base import AIModelProvider

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GeminiProvider(AIModelProvider):
    """Google Gemini AI model provider implementation."""

    def __init__(self, model_name: str, api_key: str, **kwargs):
        # Filter out HTTP client params before passing to base class
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k not in ["proxies", "timeout", "verify"]
        }
        super().__init__(model_name, **filtered_kwargs)
        self.api_key = api_key

        if genai is None:
            raise ImportError(
                "google-generativeai package is required for Gemini provider"
            )

        # Configure Gemini with API key only - ignore proxy settings
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def validate_credentials(self) -> bool:
        """Validate Gemini API credentials."""
        if not self.api_key:
            return False

        try:
            # Test with a minimal generation
            response = self.model.generate_content("test")
            return response.text is not None
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Gemini credentials validation failed: {e}"
            )
            return False

    def analyze_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Analyze alert data using Gemini model.

        Args:
            alert_data: Dictionary containing alert information

        Returns:
            Formatted analysis string

        Raises:
            Exception: If API call fails
        """
        prompt = self.get_sre_prompt(alert_data)

        try:
            response = self.model.generate_content(prompt)

            if response.text:
                return response.text
            else:
                # Handle cases where content might be blocked
                if response.candidates and response.candidates[0].finish_reason:
                    reason = response.candidates[0].finish_reason
                    raise Exception(f"Gemini content generation blocked: {reason}")
                else:
                    raise Exception("Gemini returned empty response")

        except Exception as e:
            if "API_KEY_INVALID" in str(e):
                raise Exception("Gemini authentication failed - check API key")
            elif "RATE_LIMIT_EXCEEDED" in str(e):
                raise Exception("Gemini rate limit exceeded - try again later")
            else:
                raise Exception(f"Gemini analysis failed: {str(e)}")
