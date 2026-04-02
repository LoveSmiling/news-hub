from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.hot_item import HotItem
from app.models.source import Source
from app.api.schemas import (
    GroupedHotResponse,
    HotItemResponse,
    PaginatedResponse,
)

router = APIRouter(prefix="/api/hot", tags=["hot"])


@router.get("", response_model=list[GroupedHotResponse])
async def get_all_hot(
    category: str | None = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest hot items grouped by source."""
    # Get all sources
    source_query = select(Source)
    if category:
        source_query = source_query.where(Source.category == category)
    result = await db.execute(source_query)
    sources = result.scalars().all()

    grouped = []
    for source in sources:
        items_query = (
            select(HotItem)
            .where(HotItem.source == source.name)
            .order_by(desc(HotItem.collected_at), HotItem.rank)
        )

        # Get the latest collected_at for this source
        latest_query = select(func.max(HotItem.collected_at)).where(
            HotItem.source == source.name
        )
        latest_result = await db.execute(latest_query)
        latest_time = latest_result.scalar()

        if latest_time:
            items_query = items_query.where(HotItem.collected_at == latest_time)

        items_result = await db.execute(items_query.limit(50))
        items = items_result.scalars().all()

        if items:
            grouped.append(
                GroupedHotResponse(
                    source=source.name,
                    display_name=source.display_name,
                    category=source.category,
                    last_collected_at=source.last_collected_at,
                    items=[HotItemResponse.model_validate(item) for item in items],
                )
            )

    return grouped


@router.get("/{source}", response_model=PaginatedResponse)
async def get_hot_by_source(
    source: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get hot items for a specific source with pagination."""
    # Count total
    count_query = select(func.count()).select_from(HotItem).where(HotItem.source == source)

    # Get the latest batch
    latest_query = select(func.max(HotItem.collected_at)).where(HotItem.source == source)
    latest_result = await db.execute(latest_query)
    latest_time = latest_result.scalar()

    if latest_time:
        count_query = count_query.where(HotItem.collected_at == latest_time)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch items
    offset = (page - 1) * page_size
    items_query = (
        select(HotItem)
        .where(HotItem.source == source)
        .order_by(HotItem.rank)
        .offset(offset)
        .limit(page_size)
    )
    if latest_time:
        items_query = items_query.where(HotItem.collected_at == latest_time)

    items_result = await db.execute(items_query)
    items = items_result.scalars().all()

    return PaginatedResponse(
        items=[HotItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
