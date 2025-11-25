import os
from typing import Optional, cast


class Config:
    """Configuration management for multi-model SRE alert system."""

    # Model Configuration
    AI_MODEL_PROVIDER: str = cast(str, os.getenv("AI_MODEL_PROVIDER", "ollama"))
    AI_MODEL_NAME: str = cast(str, os.getenv("AI_MODEL_NAME", "qwen2:0.5b"))

    # API Credentials
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    OLLAMA_BASE_URL: str = cast(
        str,
        os.getenv(
            "OLLAMA_BASE_URL", "http://ollama-service.ollama.svc.cluster.local:5000"
        ),
    )

    # Discord Configuration
    DISCORD_WEBHOOK_URL: str = os.environ["DISCORD_WEBHOOK_URL"]

    # App Configuration
    FLASK_ENV: str = cast(str, os.getenv("FLASK_ENV", "production"))
    LOG_LEVEL: str = cast(str, os.getenv("LOG_LEVEL", "INFO"))
    FLASK_HOST: str = cast(str, os.getenv("FLASK_HOST", "0.0.0.0"))
    FLASK_PORT: int = int(cast(str, os.getenv("FLASK_PORT", "5000")))
    HEALTH_CHECK_INTERVAL: int = int(
        cast(str, os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    )

    @classmethod
    def validate_provider_config(cls) -> bool:
        """Validate that required API keys are present for the selected provider."""
        provider = cls.AI_MODEL_PROVIDER.lower()

        if provider == "claude" and not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when using Claude provider")
        elif provider == "openai" and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
        elif provider == "gemini" and not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required when using Gemini provider")
        elif provider == "ollama" and not cls.OLLAMA_BASE_URL:
            raise ValueError("OLLAMA_BASE_URL is required when using Ollama provider")

        return True

    @classmethod
    def get_supported_providers(cls) -> list:
        """Return list of supported AI model providers."""
        return ["claude", "openai", "gemini", "ollama"]
