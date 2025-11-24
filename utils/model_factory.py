from typing import Dict

from config import Config
from models.base import AIModelProvider
from models.claude import ClaudeProvider
from models.gemini import GeminiProvider
from models.ollama import OllamaProvider
from models.openai import OpenAIProvider


class ModelFactory:
    """Factory class for creating AI model providers."""

    @staticmethod
    def create_provider(
        provider_name: str | None = None, model_name: str | None = None
    ) -> AIModelProvider:
        """
        Create an AI model provider based on configuration.

        Args:
            provider_name: Override provider from config (optional)
            model_name: Override model name from config (optional)

        Returns:
            AIModelProvider instance

        Raises:
            ValueError: If provider is not supported or credentials are missing
        """
        provider = (provider_name or Config.AI_MODEL_PROVIDER).lower()
        model = model_name or Config.AI_MODEL_NAME

        if provider == "ollama":
            return ModelFactory._create_ollama_provider(model)
        elif provider == "claude":
            return ModelFactory._create_claude_provider(model)
        elif provider == "openai":
            return ModelFactory._create_openai_provider(model)
        elif provider == "gemini":
            return ModelFactory._create_gemini_provider(model)
        else:
            supported = ", ".join(Config.get_supported_providers())
            raise ValueError(
                f"Unsupported provider '{provider}'. Supported providers: {supported}"
            )

    @staticmethod
    def _create_ollama_provider(model_name: str) -> OllamaProvider:
        """Create Ollama provider instance."""
        if not Config.OLLAMA_BASE_URL:
            raise ValueError("OLLAMA_BASE_URL is required for Ollama provider")

        return OllamaProvider(model_name=model_name, base_url=Config.OLLAMA_BASE_URL)

    @staticmethod
    def _create_claude_provider(model_name: str) -> ClaudeProvider:
        """Create Claude provider instance."""
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude provider")

        return ClaudeProvider(model_name=model_name, api_key=Config.ANTHROPIC_API_KEY)

    @staticmethod
    def _create_openai_provider(model_name: str) -> OpenAIProvider:
        """Create OpenAI provider instance."""
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")

        return OpenAIProvider(model_name=model_name, api_key=Config.OPENAI_API_KEY)

    @staticmethod
    def _create_gemini_provider(model_name: str) -> GeminiProvider:
        """Create Gemini provider instance."""
        if not Config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required for Gemini provider")

        return GeminiProvider(model_name=model_name, api_key=Config.GOOGLE_API_KEY)

    @staticmethod
    def get_available_providers() -> Dict[str, bool]:
        """
        Check which providers are available based on configuration.

        Returns:
            Dictionary mapping provider names to availability status
        """
        providers = {}

        try:
            ModelFactory._create_ollama_provider(Config.AI_MODEL_NAME)
            providers["ollama"] = True
        except ValueError:
            providers["ollama"] = False

        try:
            ModelFactory._create_claude_provider(Config.AI_MODEL_NAME)
            providers["claude"] = True
        except ValueError:
            providers["claude"] = False

        try:
            ModelFactory._create_openai_provider(Config.AI_MODEL_NAME)
            providers["openai"] = True
        except ValueError:
            providers["openai"] = False

        try:
            ModelFactory._create_gemini_provider(Config.AI_MODEL_NAME)
            providers["gemini"] = True
        except ValueError:
            providers["gemini"] = False

        return providers
