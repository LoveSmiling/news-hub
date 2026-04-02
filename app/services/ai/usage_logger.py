"""AI usage logging service - records token consumption and call results."""

import logging
import time
from contextlib import asynccontextmanager

from app.db.database import async_session
from app.models.ai_usage_log import AIUsageLog

logger = logging.getLogger(__name__)


async def log_usage(
    action: str,
    provider_type: str,
    provider_name: str | None = None,
    model: str | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    latency_ms: int | None = None,
    success: bool = True,
    error_message: str | None = None,
    meta: dict | None = None,
) -> None:
    """Write one usage log row (fire-and-forget, never raises)."""
    try:
        async with async_session() as session:
            session.add(AIUsageLog(
                action=action,
                provider_type=provider_type,
                provider_name=provider_name,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message,
                meta=meta,
            ))
            await session.commit()
    except Exception:
        logger.debug("Failed to write AI usage log", exc_info=True)


class Timer:
    """Simple wall-clock timer for measuring latency."""

    def __init__(self) -> None:
        self._start = time.monotonic()

    @property
    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self._start) * 1000)
