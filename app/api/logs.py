from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import select, func, and_, desc, case

from app.db.database import async_session
from app.models.ai_usage_log import AIUsageLog

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def get_logs(
    action: Optional[str] = Query(None, description="Filter by action type"),
    provider_type: Optional[str] = Query(None, description="Filter by llm/embedding"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=200),
):
    """Get AI usage logs with filtering and pagination."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    async with async_session() as session:
        query = select(AIUsageLog).where(AIUsageLog.created_at >= since)

        if action:
            query = query.where(AIUsageLog.action == action)
        if provider_type:
            query = query.where(AIUsageLog.provider_type == provider_type)
        if success is not None:
            query = query.where(AIUsageLog.success == success)

        # Total count
        count_q = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_q)).scalar() or 0

        # Paginated results
        offset = (page - 1) * page_size
        result = await session.execute(
            query.order_by(desc(AIUsageLog.created_at))
            .offset(offset)
            .limit(page_size)
        )
        logs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": log.id,
                "action": log.action,
                "provider_type": log.provider_type,
                "provider_name": log.provider_name,
                "model": log.model,
                "prompt_tokens": log.prompt_tokens,
                "completion_tokens": log.completion_tokens,
                "total_tokens": log.total_tokens,
                "latency_ms": log.latency_ms,
                "success": log.success,
                "error_message": log.error_message,
                "meta": log.meta,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }


@router.get("/stats")
async def get_stats(
    hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
):
    """Get aggregated token usage statistics."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    async with async_session() as session:
        # Overall stats
        result = await session.execute(
            select(
                func.count().label("total_calls"),
                func.coalesce(func.sum(case((AIUsageLog.success == True, 1), else_=0)), 0).label("success_count"),
                func.coalesce(func.sum(case((AIUsageLog.success == False, 1), else_=0)), 0).label("error_count"),
                func.coalesce(func.sum(AIUsageLog.prompt_tokens), 0).label("total_prompt_tokens"),
                func.coalesce(func.sum(AIUsageLog.completion_tokens), 0).label("total_completion_tokens"),
                func.coalesce(func.sum(AIUsageLog.total_tokens), 0).label("total_tokens"),
                func.coalesce(func.avg(AIUsageLog.latency_ms), 0).label("avg_latency_ms"),
            ).where(AIUsageLog.created_at >= since)
        )
        row = result.one()

        # Per-action breakdown
        action_result = await session.execute(
            select(
                AIUsageLog.action,
                func.count().label("calls"),
                func.coalesce(func.sum(AIUsageLog.total_tokens), 0).label("tokens"),
                func.coalesce(func.sum(case((AIUsageLog.success == True, 1), else_=0)), 0).label("successes"),
                func.coalesce(func.sum(case((AIUsageLog.success == False, 1), else_=0)), 0).label("errors"),
                func.coalesce(func.avg(AIUsageLog.latency_ms), 0).label("avg_latency"),
            )
            .where(AIUsageLog.created_at >= since)
            .group_by(AIUsageLog.action)
            .order_by(func.count().desc())
        )
        actions = action_result.all()

        # Per-hour timeline (for chart)
        timeline_result = await session.execute(
            select(
                func.date_trunc("hour", AIUsageLog.created_at).label("hour"),
                func.count().label("calls"),
                func.coalesce(func.sum(AIUsageLog.total_tokens), 0).label("tokens"),
            )
            .where(AIUsageLog.created_at >= since)
            .group_by("hour")
            .order_by("hour")
        )
        timeline = timeline_result.all()

    return {
        "hours": hours,
        "overview": {
            "total_calls": row.total_calls,
            "success_count": row.success_count,
            "error_count": row.error_count,
            "total_prompt_tokens": row.total_prompt_tokens,
            "total_completion_tokens": row.total_completion_tokens,
            "total_tokens": row.total_tokens,
            "avg_latency_ms": round(row.avg_latency_ms),
        },
        "by_action": [
            {
                "action": a.action,
                "calls": a.calls,
                "tokens": a.tokens,
                "successes": a.successes,
                "errors": a.errors,
                "avg_latency_ms": round(a.avg_latency),
            }
            for a in actions
        ],
        "timeline": [
            {
                "time": t.hour.isoformat(),
                "calls": t.calls,
                "tokens": t.tokens,
            }
            for t in timeline
        ],
    }
