import logging
from typing import Any, Dict, List

from config import Config
from utils.model_factory import ModelFactory


class FallbackManager:
    """Manages fallback mechanisms for AI model providers."""

    def __init__(
        self,
        primary_provider: str | None = None,
        fallback_providers: List[str] | None = None,
    ):
        self.primary_provider = primary_provider or Config.AI_MODEL_PROVIDER
        self.fallback_providers = fallback_providers or self._get_default_fallbacks()
        self.logger = logging.getLogger(__name__)

    def _get_default_fallbacks(self) -> List[str]:
        """Get default fallback providers based on current primary provider."""
        current = Config.AI_MODEL_PROVIDER.lower()

        fallback_order = {
            "claude": ["openai", "gemini", "ollama"],
            "openai": ["claude", "gemini", "ollama"],
            "gemini": ["claude", "openai", "ollama"],
            "ollama": ["claude", "openai", "gemini"],
        }

        return fallback_order.get(current, ["ollama"])

    def analyze_with_fallback(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to analyze alert data with fallback support.

        Args:
            alert_data: Alert data to analyze

        Returns:
            Dictionary containing analysis result and metadata
        """
        providers_to_try = [self.primary_provider] + self.fallback_providers

        last_error = None

        for provider_name in providers_to_try:
            try:
                self.logger.info(f"Attempting analysis with provider: {provider_name}")

                # Create provider instance
                provider = ModelFactory.create_provider(
                    provider_name=provider_name,
                    model_name=self._get_model_for_provider(provider_name),
                )

                # Validate credentials before proceeding
                if not provider.validate_credentials():
                    self.logger.warning(
                        f"Provider {provider_name} credentials validation failed"
                    )
                    continue

                # Attempt analysis
                analysis_content = provider.analyze_alert(alert_data)

                self.logger.info(f"Analysis successful with provider: {provider_name}")

                return {
                    "success": True,
                    "analysis": analysis_content,
                    "provider_used": provider_name,
                    "model_used": provider.model_name,
                    "fallback_used": provider_name != self.primary_provider,
                }

            except Exception as e:
                self.logger.error(f"Provider {provider_name} failed: {str(e)}")
                last_error = e
                continue

        # All providers failed
        self.logger.error("All AI providers failed")
        return {
            "success": False,
            "error": f"All AI providers failed. Last error: {str(last_error)}",
            "providers_tried": providers_to_try,
        }

    def _get_model_for_provider(self, provider_name: str) -> str:
        """Get appropriate model name for each provider."""
        default_models = {
            "claude": "claude-3-haiku-20240307",
            "openai": "gpt-3.5-turbo",
            "gemini": "gemini-2.5-flash",
            "ollama": "qwen2:0.5b",
        }

        # Use configured model if it matches the provider
        if provider_name.lower() == Config.AI_MODEL_PROVIDER.lower():
            return Config.AI_MODEL_NAME

        # Otherwise use provider default
        return default_models.get(provider_name.lower(), Config.AI_MODEL_NAME)

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all available providers."""
        available_providers = ModelFactory.get_available_providers()
        status = {}

        for provider_name, is_available in available_providers.items():
            try:
                if is_available:
                    provider = ModelFactory.create_provider(
                        provider_name=provider_name,
                        model_name=self._get_model_for_provider(provider_name),
                    )
                    credentials_valid = provider.validate_credentials()

                    status[provider_name] = {
                        "available": True,
                        "credentials_valid": credentials_valid,
                        "model": provider.model_name,
                        "ready": credentials_valid,
                    }
                else:
                    status[provider_name] = {
                        "available": False,
                        "credentials_valid": False,
                        "model": None,
                        "ready": False,
                    }
            except Exception as e:
                status[provider_name] = {
                    "available": False,
                    "credentials_valid": False,
                    "model": None,
                    "ready": False,
                    "error": str(e),
                }

        return status
