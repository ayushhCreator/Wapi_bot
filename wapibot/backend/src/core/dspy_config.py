"""DSPy LLM configuration with multi-provider support.

Supports Ollama, OpenRouter, and OpenAI.
Switch providers by changing PRIMARY_LLM_PROVIDER in .env.txt
"""

import dspy
import logging
from contextlib import contextmanager
from core.config import settings

logger = logging.getLogger(__name__)


class DSPyConfigurator:
    """Manages DSPy LLM configuration across multiple providers."""

    def __init__(self):
        self.primary_lm = None
        self.provider = settings.primary_llm_provider

    def _get_ollama_lm(self) -> dspy.LM:
        """Initialize Ollama LLM."""
        model_name = f"ollama_chat/{settings.ollama_model}"
        logger.info(f"Initializing Ollama: {model_name}")

        return dspy.LM(
            model=model_name,
            api_base=settings.ollama_base_url,
            api_key="",  # Ollama doesn't need API key
            timeout=settings.ollama_timeout,
            max_retries=settings.ollama_max_retries,
        )

    def _get_openrouter_lm(self) -> dspy.LM:
        """Initialize OpenRouter LLM with failover."""
        model_name = f"openrouter/{settings.openrouter_model}"
        logger.info(f"Initializing OpenRouter: {model_name}")

        return dspy.LM(model=model_name, api_base=settings.openrouter_base_url, api_key=settings.openrouter_api_key, timeout=settings.openrouter_timeout, extra_headers={"HTTP-Referer": settings.openrouter_site_url, "X-Title": settings.openrouter_app_name})

    def _get_openai_lm(self) -> dspy.LM:
        """Initialize OpenAI LLM."""
        logger.info(f"Initializing OpenAI: {settings.openai_model}")

        return dspy.LM(model=settings.openai_model, api_key=settings.openai_api_key, timeout=settings.openai_timeout)

    def configure(self):
        """Configure primary LLM based on settings."""
        if self.provider == "ollama":
            self.primary_lm = self._get_ollama_lm()
        elif self.provider == "openrouter":
            self.primary_lm = self._get_openrouter_lm()
        elif self.provider == "openai":
            self.primary_lm = self._get_openai_lm()
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        # Set as default LLM for DSPy
        dspy.configure(lm=self.primary_lm)
        logger.info(f"✅ DSPy configured with {self.provider}")

    @contextmanager
    def use_provider(self, provider: str):
        """Temporarily switch to different LLM provider."""
        if provider == "ollama":
            temp_lm = self._get_ollama_lm()
        elif provider == "openrouter":
            temp_lm = self._get_openrouter_lm()
        elif provider == "openai":
            temp_lm = self._get_openai_lm()
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Temporarily switch LLM
        original_lm = dspy.settings.lm
        dspy.configure(lm=temp_lm)

        try:
            yield temp_lm
        finally:
            # Restore original LLM
            dspy.configure(lm=original_lm)


# Global configurator instance
dspy_configurator = DSPyConfigurator()
