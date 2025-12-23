"""Application configuration with Pydantic Settings.

Supports Ollama, OpenRouter, and OpenAI providers.
Switch provider by changing PRIMARY_LLM_PROVIDER in .env.txt
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env.txt",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "WapiBot Backend V2"
    app_version: str = "2.0.0"
    debug: bool = True
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./conversations.db"
    checkpoint_db_path: str = "./checkpoints.db"

    # LLM Provider Selection
    primary_llm_provider: Literal["ollama", "openrouter", "openai"] = "ollama"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    ollama_timeout: float = 30.0
    ollama_max_retries: int = 2

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_fallback_model: str = "anthropic/claude-3.5-haiku"
    openrouter_app_name: str = "WapiBot"
    openrouter_site_url: str = ""
    openrouter_timeout: float = 60.0

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_timeout: float = 30.0

    # DSPy
    dspy_cache_dir: str = "./dspy_cache"
    dspy_max_tokens: int = 2000
    dspy_temperature: float = 0.7

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Feature Flags
    enable_sentiment_analysis: bool = True
    enable_intent_classification: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
