"""Dynamic AI configuration service with in-memory cache and hot-reload.

Reads LLM / Embedding provider configs from the ai_configs table.
Caches them in memory. Any update via the API invalidates the cache
so the next call picks up new settings without restarting.
"""

import logging
from dataclasses import dataclass

from sqlalchemy import select, and_

from app.db.database import async_session
from app.models.ai_config import AIConfig

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    id: int
    name: str
    provider_type: str  # "llm" | "embedding"
    api_base: str
    api_key: str | None
    model: str
    enabled: bool
    is_default: bool
    extra: dict | None


# ---- in-memory cache ----
_cache: dict[str, list[ProviderConfig]] = {}  # keyed by provider_type
_version: int = 0  # bumped on every invalidation


def invalidate_cache() -> None:
    """Call after any write to ai_configs to force reload on next access."""
    global _cache, _version
    _cache.clear()
    _version += 1
    logger.info("AI config cache invalidated (v%d)", _version)


async def _load_configs(provider_type: str) -> list[ProviderConfig]:
    """Load configs from DB for a given type."""
    async with async_session() as session:
        result = await session.execute(
            select(AIConfig)
            .where(
                and_(
                    AIConfig.provider_type == provider_type,
                    AIConfig.enabled.is_(True),
                )
            )
            .order_by(AIConfig.is_default.desc(), AIConfig.id)
        )
        rows = result.scalars().all()

    configs = [
        ProviderConfig(
            id=r.id,
            name=r.name,
            provider_type=r.provider_type,
            api_base=r.api_base,
            api_key=r.api_key,
            model=r.model,
            enabled=r.enabled,
            is_default=r.is_default,
            extra=r.extra,
        )
        for r in rows
    ]
    _cache[provider_type] = configs
    return configs


async def get_default_config(provider_type: str) -> ProviderConfig | None:
    """Return the default (or first enabled) config for the given type.

    Results are cached; call ``invalidate_cache()`` after writes.
    """
    if provider_type in _cache:
        configs = _cache[provider_type]
    else:
        configs = await _load_configs(provider_type)

    if not configs:
        return None
    # First one is already the default (ORDER BY is_default DESC)
    return configs[0]


async def get_all_configs(provider_type: str | None = None) -> list[ProviderConfig]:
    """Return all enabled configs, optionally filtered by type."""
    if provider_type:
        if provider_type in _cache:
            return _cache[provider_type]
        return await _load_configs(provider_type)

    # Load both types
    llm = await _load_configs("llm") if "llm" not in _cache else _cache["llm"]
    emb = await _load_configs("embedding") if "embedding" not in _cache else _cache["embedding"]
    return llm + emb
