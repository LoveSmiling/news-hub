import logging

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

EMBED_DIM = 1024  # bge-m3 default dimension


async def _get_embed_client_and_model() -> tuple[AsyncOpenAI, str]:
    """Resolve the embedding provider from DB config, falling back to env."""
    from app.services.ai.config_service import get_default_config
    from app.services.ai.llm_client import _make_client

    cfg = await get_default_config("embedding")
    if cfg:
        return _make_client(cfg.api_base, cfg.api_key), cfg.model
    # Fallback: same endpoint as LLM settings
    return _make_client(settings.ollama_url, None), "bge-large-zh-v1.5"


async def get_embedding(text: str, model: str | None = None, log_meta: dict | None = None) -> list[float]:
    """Get text embedding via the configured embedding provider."""
    from app.services.ai.config_service import get_default_config
    from app.services.ai.usage_logger import log_usage, Timer

    client, default_model = await _get_embed_client_and_model()
    use_model = model or default_model

    cfg = await get_default_config("embedding")
    provider_name = cfg.name if cfg else "env_fallback"

    timer = Timer()
    try:
        response = await client.embeddings.create(
            input=text,
            model=use_model,
        )
        usage = response.usage
        await log_usage(
            action="embedding",
            provider_type="embedding",
            provider_name=provider_name,
            model=use_model,
            prompt_tokens=usage.prompt_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            latency_ms=timer.elapsed_ms,
            success=True,
            meta=log_meta,
        )
        return response.data[0].embedding
    except Exception as e:
        await log_usage(
            action="embedding",
            provider_type="embedding",
            provider_name=provider_name,
            model=use_model,
            latency_ms=timer.elapsed_ms,
            success=False,
            error_message=str(e)[:500],
            meta=log_meta,
        )
        raise


async def get_embeddings_batch(
    texts: list[str],
    model: str | None = None,
    log_meta: dict | None = None,
) -> list[list[float]]:
    """Get embeddings for multiple texts."""
    if not texts:
        return []

    from app.services.ai.config_service import get_default_config
    from app.services.ai.usage_logger import log_usage, Timer

    client, default_model = await _get_embed_client_and_model()
    use_model = model or default_model

    cfg = await get_default_config("embedding")
    provider_name = cfg.name if cfg else "env_fallback"

    timer = Timer()
    try:
        response = await client.embeddings.create(
            input=texts,
            model=use_model,
        )
        usage = response.usage
        await log_usage(
            action="embedding_batch",
            provider_type="embedding",
            provider_name=provider_name,
            model=use_model,
            prompt_tokens=usage.prompt_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            latency_ms=timer.elapsed_ms,
            success=True,
            meta={**(log_meta or {}), "batch_size": len(texts)},
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        await log_usage(
            action="embedding_batch",
            provider_type="embedding",
            provider_name=provider_name,
            model=use_model,
            latency_ms=timer.elapsed_ms,
            success=False,
            error_message=str(e)[:500],
            meta={**(log_meta or {}), "batch_size": len(texts)},
        )
        raise
