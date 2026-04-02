"""Content retrieval service — fetch and clean hot item content from the database."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import select, or_, func

from app.db.database import async_session
from app.models.hot_item import HotItem
from app.utils.html_cleaner import clean_html, truncate_text

logger = logging.getLogger(__name__)


@dataclass
class ContentItem:
    """Cleaned content item returned by retrieve_contents."""

    id: int
    title: str
    source: str
    url: str
    content: str
    collected_at: datetime


async def retrieve_contents(
    *,
    source: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    keyword: Optional[str] = None,
    item_ids: Optional[list[int]] = None,
    limit: int = 50,
    max_content_chars: int = 2000,
) -> list[ContentItem]:
    """Retrieve hot items and return cleaned content.

    Supports filtering by source, time range, keyword (title or keywords JSONB),
    and item IDs. Content is extracted from raw_data->>'summary', cleaned of HTML,
    and truncated to max_content_chars.
    """
    async with async_session() as session:
        query = select(
            HotItem.id,
            HotItem.title,
            HotItem.source,
            HotItem.url,
            HotItem.raw_data["summary"].as_string().label("raw_summary"),
            HotItem.collected_at,
        )

        if source:
            query = query.where(HotItem.source == source)

        if start_time:
            query = query.where(HotItem.collected_at >= start_time)

        if end_time:
            query = query.where(HotItem.collected_at <= end_time)

        if keyword:
            kw_lower = keyword.lower()
            query = query.where(
                or_(
                    func.lower(HotItem.title).contains(kw_lower),
                    HotItem.keywords.op("@>")(f'["{keyword}"]'),
                )
            )

        if item_ids:
            query = query.where(HotItem.id.in_(item_ids))

        query = query.order_by(HotItem.collected_at.desc()).limit(limit)

        result = await session.execute(query)
        rows = result.all()

    items: list[ContentItem] = []
    for row in rows:
        raw = row.raw_summary or ""
        content = clean_html(raw)
        content = truncate_text(content, max_content_chars)
        items.append(
            ContentItem(
                id=row.id,
                title=row.title,
                source=row.source,
                url=row.url,
                content=content,
                collected_at=row.collected_at,
            )
        )

    return items
