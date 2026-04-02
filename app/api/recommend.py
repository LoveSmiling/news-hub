from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.hot_item import HotItem
from app.api.schemas import HotItemResponse

router = APIRouter(prefix="/api/recommend", tags=["recommend"])


@router.post("")
async def get_recommendations(
    categories: list[str] = Body(default=[], embed=True),
    read_item_ids: list[int] = Body(default=[], embed=True),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get personalized recommendations based on user preferences.

    - categories: preferred categories (from localStorage)
    - read_item_ids: recently read item IDs (for exclusion and interest signal)
    """
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    query = (
        select(HotItem)
        .where(HotItem.collected_at >= since)
        .order_by(desc(HotItem.collected_at), HotItem.rank.asc().nullslast())
    )

    # If categories specified, prioritize those
    if categories:
        query = query.where(HotItem.category.in_(categories))

    # Exclude already-read items
    if read_item_ids:
        query = query.where(HotItem.id.notin_(read_item_ids[:100]))

    query = query.limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    # Cold start: if no results with category filter, fall back to all
    if not items and categories:
        fallback_query = (
            select(HotItem)
            .where(HotItem.collected_at >= since)
            .order_by(desc(HotItem.collected_at), HotItem.rank.asc().nullslast())
        )
        if read_item_ids:
            fallback_query = fallback_query.where(
                HotItem.id.notin_(read_item_ids[:100])
            )
        fallback_query = fallback_query.limit(limit)
        result = await db.execute(fallback_query)
        items = result.scalars().all()

    return {
        "items": [HotItemResponse.model_validate(it) for it in items],
        "strategy": "category_filter" if categories else "cold_start",
    }
