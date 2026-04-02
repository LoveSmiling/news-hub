import logging

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# ---- client cache keyed by (api_base, api_key) ----
_clients: dict[tuple[str, str | None], AsyncOpenAI] = {}


def _make_client(api_base: str, api_key: str | None) -> AsyncOpenAI:
    key = (api_base, api_key)
    if key not in _clients:
        _clients[key] = AsyncOpenAI(
            base_url=f"{api_base.rstrip('/')}/v1",
            api_key=api_key or "no-key",
        )
    return _clients[key]


async def get_llm_client() -> AsyncOpenAI:
    """Get an AsyncOpenAI client from the active DB config, falling back to env vars."""
    from app.services.ai.config_service import get_default_config

    cfg = await get_default_config("llm")
    if cfg:
        return _make_client(cfg.api_base, cfg.api_key)
    # Fallback to env / static settings
    return _make_client(settings.ollama_url, None)


async def get_llm_model() -> str:
    """Return the model name from the active DB config, falling back to env."""
    from app.services.ai.config_service import get_default_config

    cfg = await get_default_config("llm")
    if cfg:
        return cfg.model
    return settings.ollama_model


async def chat_completion(
    prompt: str,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    action: str = "chat",
    log_meta: dict | None = None,
    enable_thinking: bool = True,
) -> str:
    """Send a chat completion request and return the text response."""
    from app.services.ai.config_service import get_default_config
    from app.services.ai.usage_logger import log_usage, Timer

    client = await get_llm_client()
    model = model or await get_llm_model()

    cfg = await get_default_config("llm")
    provider_name = cfg.name if cfg else "env_fallback"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    timer = Timer()
    try:
        kwargs: dict = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if not enable_thinking:
            # /no_think in prompt handles Qwen3 on any backend.
            # extra_body handles DeepSeek/others on vLLM, but breaks Ollama.
            api_base = cfg.api_base if cfg else settings.ollama_url
            if ":11434" not in api_base:
                kwargs["extra_body"] = {
                    "enable_thinking": False,
                    "chat_template_kwargs": {"enable_thinking": False},
                }
        response = await client.chat.completions.create(**kwargs)
        usage = response.usage
        await log_usage(
            action=action,
            provider_type="llm",
            provider_name=provider_name,
            model=model,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            latency_ms=timer.elapsed_ms,
            success=True,
            meta=log_meta,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        await log_usage(
            action=action,
            provider_type="llm",
            provider_name=provider_name,
            model=model,
            latency_ms=timer.elapsed_ms,
            success=False,
            error_message=str(e)[:500],
            meta=log_meta,
        )
        logger.exception("LLM chat completion failed (model=%s)", model)
        raise
