from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hot_item import HotItem


async def find_duplicate(
    session: AsyncSession,
    source: str,
    url: str,
    since: datetime,
) -> HotItem | None:
    """Find an existing hot item by source + url since a given time."""
    result = await session.execute(
        select(HotItem).where(
            and_(
                HotItem.source == source,
                HotItem.url == url,
                HotItem.collected_at >= since,
            )
        )
    )
    return result.scalar_one_or_none()
