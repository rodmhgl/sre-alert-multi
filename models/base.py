from abc import ABC, abstractmethod
from typing import Any, Dict


class AIModelProvider(ABC):
    """Abstract base class for AI model providers."""

    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs

    @abstractmethod
    def analyze_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Analyze alert data and return SRE analysis.

        Args:
            alert_data: Dictionary containing alert information

        Returns:
            Formatted analysis string ready for Discord
        """
        pass

    def get_sre_prompt(self, alert_data: Dict[str, Any]) -> str:
        """
        Generate the standardized SRE analysis prompt.

        Args:
            alert_data: Dictionary containing alert information

        Returns:
            Formatted prompt string
        """
        return self._load_prompt_template().format(alert_data=alert_data)

    def _load_prompt_template(self) -> str:
        """Load the SRE prompt template from file."""
        import os

        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "sre_analysis.md"
        )

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to basic prompt if file not found
            return """Analyze the alert data and provide SRE insights.

Alert Data: {alert_data}"""

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate that the provider has the necessary credentials/configuration.

        Returns:
            True if credentials are valid, False otherwise
        """
        pass

    def get_provider_name(self) -> str:
        """Return the name of the provider."""
        return self.__class__.__name__.replace("Provider", "").lower()

    def get_model_info(self) -> Dict[str, Any]:
        """Return information about the current model configuration."""
        return {
            "provider": self.get_provider_name(),
            "model_name": self.model_name,
            "config": self.config,
        }
