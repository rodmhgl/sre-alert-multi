from typing import TYPE_CHECKING, Any, Dict

from .base import AIModelProvider

if TYPE_CHECKING:
    import anthropic
else:
    try:
        import anthropic
    except ImportError:
        anthropic = None


class ClaudeProvider(AIModelProvider):
    """Anthropic Claude AI model provider implementation."""

    def __init__(self, model_name: str, api_key: str, **kwargs):
        # Filter out HTTP client params before passing to base class
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k not in ["proxies", "timeout", "verify"]
        }
        super().__init__(model_name, **filtered_kwargs)
        self.api_key = api_key

        if anthropic is None:
            raise ImportError("anthropic package is required for Claude provider")

        # Clear proxy environment variables that Docker might set
        import os

        original_env = {}
        proxy_vars = [
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "http_proxy",
            "https_proxy",
            "NO_PROXY",
            "no_proxy",
        ]
        for var in proxy_vars:
            if var in os.environ:
                original_env[var] = os.environ[var]
                del os.environ[var]

        try:
            self.client = anthropic.Anthropic(api_key=api_key)
        finally:
            # Restore environment variables
            for var, value in original_env.items():
                os.environ[var] = value

    def validate_credentials(self) -> bool:
        """Validate Claude API credentials."""
        if not self.api_key:
            return False

        try:
            # Test with a minimal message
            self.client.messages.create(
                model=self.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception:
            return False

    def analyze_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Analyze alert data using Claude model.

        Args:
            alert_data: Dictionary containing alert information

        Returns:
            Formatted analysis string

        Raises:
            Exception: If API call fails
        """
        assert anthropic is not None
        prompt = self.get_sre_prompt(alert_data)

        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text content from response
            analysis_content = ""
            for content in response.content:
                text = getattr(content, "text", None)
                if text is not None:
                    analysis_content += text

            return analysis_content or "No analysis available"

        except anthropic.AuthenticationError:
            raise Exception("Claude authentication failed - check API key")
        except anthropic.RateLimitError:
            raise Exception("Claude rate limit exceeded - try again later")
        except anthropic.APIError as e:
            raise Exception(f"Claude API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Claude analysis failed: {str(e)}")
