"""Hot topic burst detection service.

Detects topics experiencing sudden popularity spikes or multi-platform emergence.
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session
from app.models.hot_item import HotItem

logger = logging.getLogger(__name__)


async def detect_bursts(
    window_hours: int = 6,
    baseline_hours: int = 48,
    min_ratio: float = 2.0,
    limit: int = 10,
) -> list[dict]:
    """Detect burst topics by comparing recent vs baseline keyword frequency.

    A burst is detected when a keyword's frequency in the recent window
    is significantly higher (>= min_ratio) than its baseline frequency.
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=window_hours)
    baseline_start = now - timedelta(hours=baseline_hours)

    async with async_session() as session:
        # Recent items (window)
        recent_result = await session.execute(
            select(HotItem).where(
                and_(
                    HotItem.collected_at >= window_start,
                    HotItem.keywords.isnot(None),
                )
            )
        )
        recent_items = recent_result.scalars().all()

        # Baseline items (older period)
        baseline_result = await session.execute(
            select(HotItem).where(
                and_(
                    HotItem.collected_at >= baseline_start,
                    HotItem.collected_at < window_start,
                    HotItem.keywords.isnot(None),
                )
            )
        )
        baseline_items = baseline_result.scalars().all()

    # Count keyword frequencies
    recent_kw: Counter[str] = Counter()
    baseline_kw: Counter[str] = Counter()

    for item in recent_items:
        if item.keywords:
            for kw in item.keywords:
                recent_kw[kw] += 1

    for item in baseline_items:
        if item.keywords:
            for kw in item.keywords:
                baseline_kw[kw] += 1

    # Normalize baseline to same time scale
    if baseline_hours > window_hours:
        scale = window_hours / (baseline_hours - window_hours)
    else:
        scale = 1.0

    # Find bursting keywords
    bursts = []
    for kw, recent_count in recent_kw.most_common():
        baseline_count = baseline_kw.get(kw, 0) * scale
        if baseline_count < 1:
            baseline_count = 0.5  # Avoid division by zero; treat as new keyword

        ratio = recent_count / baseline_count

        if ratio >= min_ratio and recent_count >= 2:
            # Collect related items
            related = [
                it for it in recent_items
                if it.keywords and kw in it.keywords
            ]
            sources = list({it.source for it in related})

            bursts.append({
                "keyword": kw,
                "burst_ratio": round(ratio, 1),
                "recent_count": recent_count,
                "sources": sources,
                "source_count": len(sources),
                "items": [
                    {
                        "id": it.id,
                        "source": it.source,
                        "title": it.title,
                        "url": it.url,
                        "collected_at": it.collected_at.isoformat(),
                    }
                    for it in related[:5]
                ],
            })

        if len(bursts) >= limit:
            break

    bursts.sort(key=lambda b: b["burst_ratio"], reverse=True)
    return bursts


async def get_hot_value_trend(
    source: str,
    hours: int = 24,
) -> list[dict]:
    """Get hot value trend data for a source over time (for charting)."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    async with async_session() as session:
        result = await session.execute(
            select(
                func.date_trunc("hour", HotItem.collected_at).label("hour"),
                func.count().label("item_count"),
            )
            .where(
                and_(
                    HotItem.source == source,
                    HotItem.collected_at >= since,
                )
            )
            .group_by("hour")
            .order_by("hour")
        )
        rows = result.all()

    return [
        {"time": row.hour.isoformat(), "count": row.item_count}
        for row in rows
    ]
