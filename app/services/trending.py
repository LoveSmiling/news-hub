"""Trending topic aggregation service.

Groups hot items into trending topics based on keyword overlap and embedding similarity.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session
from app.models.hot_item import HotItem

logger = logging.getLogger(__name__)


async def get_trending_topics(
    hours: int = 24,
    min_sources: int = 2,
    limit: int = 20,
) -> list[dict]:
    """Detect trending topics that appear across multiple sources.

    A topic is considered trending when it appears on 2+ different sources
    within the time window, detected via keyword overlap.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    async with async_session() as session:
        # Get recent items that have keywords
        result = await session.execute(
            select(HotItem)
            .where(
                and_(
                    HotItem.collected_at >= since,
                    HotItem.keywords.isnot(None),
                )
            )
            .order_by(HotItem.collected_at.desc())
            .limit(500)
        )
        items = result.scalars().all()

    if not items:
        return []

    # Group items by shared keywords
    keyword_groups: dict[str, list] = defaultdict(list)
    for item in items:
        if not item.keywords:
            continue
        for kw in item.keywords:
            keyword_groups[kw].append(item)

    # Find keywords that span multiple sources
    topics = []
    seen_keywords = set()

    for kw, group_items in sorted(
        keyword_groups.items(), key=lambda x: len(x[1]), reverse=True
    ):
        if kw in seen_keywords:
            continue

        sources = {it.source for it in group_items}
        if len(sources) < min_sources:
            continue

        seen_keywords.add(kw)
        # Pick representative items (one per source, latest)
        source_items = {}
        for it in group_items:
            if it.source not in source_items:
                source_items[it.source] = it

        topics.append({
            "keyword": kw,
            "source_count": len(sources),
            "sources": list(sources),
            "item_count": len(group_items),
            "items": [
                {
                    "id": it.id,
                    "source": it.source,
                    "title": it.title,
                    "url": it.url,
                    "hot_value": it.hot_value,
                    "collected_at": it.collected_at.isoformat(),
                }
                for it in source_items.values()
            ],
        })

        if len(topics) >= limit:
            break

    return topics


async def find_similar_items(
    item_id: int,
    limit: int = 10,
) -> list[dict]:
    """Find items similar to a given item using pgvector cosine similarity."""
    async with async_session() as session:
        # Get the target item's embedding
        result = await session.execute(
            select(HotItem).where(HotItem.id == item_id)
        )
        target = result.scalar_one_or_none()

        if not target or target.embedding is None:
            return []

        # Cosine similarity search via pgvector
        result = await session.execute(
            select(HotItem)
            .where(
                and_(
                    HotItem.id != item_id,
                    HotItem.embedding.isnot(None),
                )
            )
            .order_by(HotItem.embedding.cosine_distance(target.embedding))
            .limit(limit)
        )
        similar = result.scalars().all()

    return [
        {
            "id": it.id,
            "source": it.source,
            "title": it.title,
            "url": it.url,
            "category": it.category,
            "collected_at": it.collected_at.isoformat(),
        }
        for it in similar
    ]
