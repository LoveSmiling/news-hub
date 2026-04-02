from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.hot_item import HotItem
from app.api.schemas import PaginatedResponse, HotItemResponse

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=PaginatedResponse)
async def search_hot_items(
    q: str = Query(..., min_length=1, max_length=200, description="搜索关键词"),
    source: str | None = Query(None, description="按来源过滤"),
    category: str | None = Query(None, description="按分类过滤"),
    start_date: datetime | None = Query(None, description="开始时间"),
    end_date: datetime | None = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Full-text search on hot item titles with optional filters."""
    # Build tsquery from search terms — use 'simple' config for CJK support
    # Split query into words and join with &
    terms = q.strip().split()
    tsquery_str = " & ".join(terms)

    base = select(HotItem).where(
        HotItem.title_tsv.op("@@")(func.to_tsquery("simple", tsquery_str))
    )

    count_query = select(func.count()).select_from(
        base.subquery()
    )

    # Apply filters
    if source:
        base = base.where(HotItem.source == source)
        count_query = select(func.count()).select_from(base.subquery())
    if category:
        base = base.where(HotItem.category == category)
        count_query = select(func.count()).select_from(base.subquery())
    if start_date:
        base = base.where(HotItem.collected_at >= start_date)
        count_query = select(func.count()).select_from(base.subquery())
    if end_date:
        base = base.where(HotItem.collected_at <= end_date)
        count_query = select(func.count()).select_from(base.subquery())

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results, ordered by relevance then time
    items_query = (
        base.order_by(
            desc(
                func.ts_rank(
                    HotItem.title_tsv,
                    func.to_tsquery("simple", tsquery_str),
                )
            ),
            desc(HotItem.collected_at),
        )
        .offset((page - 1) * size)
        .limit(size)
    )

    result = await db.execute(items_query)
    items = result.scalars().all()

    return PaginatedResponse(
        items=[HotItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=size,
    )
