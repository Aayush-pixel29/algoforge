"""LLM factory — swap Ollama / OpenAI / Anthropic without touching agents."""

from __future__ import annotations

from typing import Any

from algoforge.config import Settings


def build_llm(settings: Settings) -> Any:
    """Build a CrewAI native LLM from the provider settings."""
    provider = settings.llm_provider.lower().strip()
    model = settings.llm_model

    from crewai import LLM

    if provider == "ollama":
        # Litellm requires the 'ollama/' prefix for Ollama models
        if not model.startswith("ollama/"):
            model = f"ollama/{model}"
        return LLM(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=0.2,
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return LLM(
            model=model,
            api_key=settings.openai_api_key,
            temperature=0.2,
        )

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        if not model.startswith("anthropic/"):
            model = f"anthropic/{model}"
        return LLM(
            model=model,
            api_key=settings.anthropic_api_key,
            temperature=0.2,
        )

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        if not model.startswith("gemini/"):
            model = f"gemini/{model}"
        return LLM(
            model=model,
            api_key=settings.gemini_api_key,
            temperature=0.2,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider!r}. Use ollama|openai|anthropic|gemini.")
