"""LLM factory — swap Ollama / OpenAI / Anthropic without touching agents."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from algoforge.config import Settings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


def build_llm(settings: Settings) -> Any:
    """Build a LangChain chat model from the provider settings."""
    provider = settings.llm_provider.lower().strip()
    model = settings.llm_model

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=model,
                base_url=settings.ollama_base_url,
                temperature=0.2,
            )
        except ImportError:
            from langchain_community.llms import Ollama

            return Ollama(model=model, base_url=settings.ollama_base_url)

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return ChatOpenAI(model=model, api_key=settings.openai_api_key, temperature=0.2)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        return ChatAnthropic(model=model, api_key=settings.anthropic_api_key, temperature=0.2)

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider!r}. Use ollama|openai|anthropic.")
