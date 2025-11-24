from typing import TYPE_CHECKING, Any, Dict

from .base import AIModelProvider

if TYPE_CHECKING:
    import openai
else:
    try:
        import openai
    except ImportError:
        openai = None


class OpenAIProvider(AIModelProvider):
    """OpenAI ChatGPT model provider implementation."""

    def __init__(self, model_name: str, api_key: str, **kwargs):
        # Filter out HTTP client params before passing to base class
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k not in ["proxies", "timeout", "verify"]
        }
        super().__init__(model_name, **filtered_kwargs)
        self.api_key = api_key

        if openai is None:
            raise ImportError("openai package is required for OpenAI provider")

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
            self.client = openai.OpenAI(api_key=api_key)
        finally:
            # Restore environment variables
            for var, value in original_env.items():
                os.environ[var] = value

    def validate_credentials(self) -> bool:
        """Validate OpenAI API credentials."""
        if not self.api_key:
            return False

        try:
            # Test with a minimal completion
            self.client.chat.completions.create(
                model=self.model_name,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception:
            return False

    def analyze_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Analyze alert data using OpenAI model.

        Args:
            alert_data: Dictionary containing alert information

        Returns:
            Formatted analysis string

        Raises:
            Exception: If API call fails
        """
        assert openai is not None
        prompt = self.get_sre_prompt(alert_data)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            analysis_content = response.choices[0].message.content
            return analysis_content or "No analysis available"

        except openai.AuthenticationError:
            raise Exception("OpenAI authentication failed - check API key")
        except openai.RateLimitError:
            raise Exception("OpenAI rate limit exceeded - try again later")
        except openai.APIError as e:
            raise Exception(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise Exception(f"OpenAI analysis failed: {str(e)}")
