import json
from typing import Any, Dict

import requests

from .base import AIModelProvider


class OllamaProvider(AIModelProvider):
    """Ollama AI model provider implementation."""

    def __init__(self, model_name: str, base_url: str, **kwargs):
        super().__init__(model_name, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/chat"

    def validate_credentials(self) -> bool:
        """Validate Ollama server accessibility."""
        try:
            test_payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "test"}],
                "stream": False,
            }

            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(test_payload),
                timeout=90,  # Increased timeout for slow Ollama responses
            )

            return response.status_code == 200
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"Ollama validation failed: {e}")
            return False

    def analyze_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Analyze alert data using Ollama model.

        Args:
            alert_data: Dictionary containing alert information

        Returns:
            Formatted analysis string

        Raises:
            Exception: If API call fails
        """
        prompt = self.get_sre_prompt(alert_data)

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        try:
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=90,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Ollama API error: {response.status_code} - {response.text}"
                )

            response_data = response.json()
            analysis_content = response_data.get("message", {}).get(
                "content", "No analysis available"
            )

            return analysis_content

        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from Ollama: {str(e)}")
        except Exception as e:
            raise Exception(f"Ollama analysis failed: {str(e)}")
