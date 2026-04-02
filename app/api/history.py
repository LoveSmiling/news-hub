from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.hot_item import HotItem
from app.api.schemas import PaginatedResponse, HotItemResponse

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/dates/{source}")
async def get_available_dates(
    source: str,
    db: AsyncSession = Depends(get_db),
):
    """Get list of dates that have historical data for a source."""
    query = (
        select(cast(HotItem.collected_at, Date).label("date"))
        .where(HotItem.source == source)
        .group_by(cast(HotItem.collected_at, Date))
        .order_by(desc(cast(HotItem.collected_at, Date)))
        .limit(90)
    )
    result = await db.execute(query)
    dates = [row[0].isoformat() for row in result.all()]
    return {"source": source, "dates": dates}


@router.get("/{source}/{date_str}", response_model=PaginatedResponse)
async def get_history_snapshot(
    source: str,
    date_str: date,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get historical hot items for a source on a specific date.

    Returns the latest snapshot collected on that date.
    """
    day_start = datetime.combine(date_str, time.min, tzinfo=timezone.utc)
    day_end = datetime.combine(date_str, time.max, tzinfo=timezone.utc)

    # Find the latest collection time on this date for this source
    latest_query = (
        select(func.max(HotItem.collected_at))
        .where(HotItem.source == source)
        .where(HotItem.collected_at >= day_start)
        .where(HotItem.collected_at <= day_end)
    )
    latest_result = await db.execute(latest_query)
    latest_time = latest_result.scalar()

    if not latest_time:
        return PaginatedResponse(items=[], total=0, page=page, page_size=size)

    # Get items from that collection snapshot
    base = (
        select(HotItem)
        .where(HotItem.source == source)
        .where(HotItem.collected_at == latest_time)
    )

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0

    items_query = base.order_by(HotItem.rank).offset((page - 1) * size).limit(size)
    result = await db.execute(items_query)
    items = result.scalars().all()

    return PaginatedResponse(
        items=[HotItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=size,
    )
