from fastapi import APIRouter, Query

from app.services.trending import get_trending_topics, find_similar_items
from app.services.burst_detector import detect_bursts, get_hot_value_trend

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("")
async def get_trends(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    min_sources: int = Query(2, ge=1, description="Min sources for a topic"),
    limit: int = Query(20, ge=1, le=50),
):
    """Get trending topics across multiple sources."""
    topics = await get_trending_topics(
        hours=hours, min_sources=min_sources, limit=limit
    )
    return {"topics": topics, "hours": hours}


@router.get("/bursts")
async def get_bursts(
    window: int = Query(6, ge=1, le=48, description="Recent window hours"),
    limit: int = Query(10, ge=1, le=30),
):
    """Get burst/spike topics."""
    bursts = await detect_bursts(window_hours=window, limit=limit)
    return {"bursts": bursts, "window_hours": window}


@router.get("/hot-curve/{source}")
async def get_hot_curve(
    source: str,
    hours: int = Query(24, ge=1, le=168),
):
    """Get hot value trend data for a source (for chart rendering)."""
    data = await get_hot_value_trend(source=source, hours=hours)
    return {"source": source, "hours": hours, "data": data}


@router.get("/similar/{item_id}")
async def get_similar(
    item_id: int,
    limit: int = Query(10, ge=1, le=30),
):
    """Find items similar to a given item using embedding similarity."""
    items = await find_similar_items(item_id=item_id, limit=limit)
    return {"item_id": item_id, "similar": items}
