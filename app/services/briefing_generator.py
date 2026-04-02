"""Briefing generation service.

Provides functions to generate briefings of different types (source, daily,
topic, custom) using the Map-Reduce summarization pipeline.  Each function
creates a Briefing DB record, runs generation in the background via
asyncio.create_task, and updates the record on completion or failure.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.sql import func

from app.db.database import async_session
from app.models.briefing import Briefing, BriefingItem
from app.models.source import Source
from app.services.content_service import retrieve_contents
from app.services.ai.map_reduce_summarizer import map_reduce_summarize

logger = logging.getLogger(__name__)


async def _build_display_map() -> dict[str, str]:
    """Query Source table and return {name: display_name} mapping."""
    async with async_session() as session:
        result = await session.execute(select(Source.name, Source.display_name))
        return {row.name: row.display_name for row in result.all()}


# ── Internal helpers ──────────────────────────────────────────────

async def _create_briefing(
    title: str,
    brief_type: str,
    scope_params: dict | None = None,
) -> Briefing:
    """Insert a new briefing record with status='generating'."""
    async with async_session() as session:
        briefing = Briefing(
            title=title,
            brief_type=brief_type,
            scope_params=scope_params,
            status="generating",
        )
        session.add(briefing)
        await session.commit()
        await session.refresh(briefing)
        return briefing


async def _finish_briefing(
    briefing_id: int,
    content: str,
    item_ids: list[int],
) -> None:
    """Mark a briefing as done and save associated item IDs."""
    async with async_session() as session:
        await session.execute(
            update(Briefing)
            .where(Briefing.id == briefing_id)
            .values(
                content=content,
                status="done",
                completed_at=func.now(),
            )
        )
        for item_id in item_ids:
            session.add(BriefingItem(briefing_id=briefing_id, hot_item_id=item_id))
        await session.commit()


async def _fail_briefing(briefing_id: int, error: str) -> None:
    """Mark a briefing as failed with error info."""
    async with async_session() as session:
        await session.execute(
            update(Briefing)
            .where(Briefing.id == briefing_id)
            .values(
                content=f"生成失败：{error}",
                status="failed",
                completed_at=func.now(),
            )
        )
        await session.commit()


async def _run_generation(
    briefing_id: int,
    items_coro,
    display_map: dict[str, str] | None = None,
) -> None:
    """Background task: fetch items, run Map-Reduce, update briefing.

    ``items_coro`` is an awaitable that returns list[ContentItem].
    """
    try:
        items = await items_coro
        if not items:
            await _finish_briefing(briefing_id, "该范围内暂无数据。", [])
            return

        content = await map_reduce_summarize(items, display_map=display_map)
        # Strip <think>...</think> blocks from reasoning models
        content = re.sub(r"<think>[\s\S]*?</think>", "", content).lstrip()
        item_ids = [it.id for it in items]
        await _finish_briefing(briefing_id, content, item_ids)
        logger.info("Briefing %d generated successfully (%d items)", briefing_id, len(items))
    except Exception as exc:
        logger.error("Briefing %d generation failed", briefing_id, exc_info=True)
        await _fail_briefing(briefing_id, str(exc))


# ── Public API ────────────────────────────────────────────────────

async def generate_source_briefing(
    source: str,
    date: str | None = None,
) -> Briefing:
    """Generate a briefing for a single source on a given date."""
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    display_map = await _build_display_map()
    display_name = display_map.get(source, source)

    title = f"{display_name} 简报 - {target_date}"
    scope_params = {"source": source, "date": target_date}

    briefing = await _create_briefing(title, "source", scope_params)

    start = datetime.fromisoformat(f"{target_date}T00:00:00+00:00")
    end = start + timedelta(days=1)

    asyncio.create_task(
        _run_generation(
            briefing.id,
            retrieve_contents(source=source, start_time=start, end_time=end, limit=50),
            display_map=display_map,
        )
    )
    return briefing


async def generate_daily_briefing(date: str | None = None) -> Briefing:
    """Generate a cross-source daily briefing."""
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = f"每日简报 - {target_date}"
    scope_params = {"date": target_date}

    briefing = await _create_briefing(title, "daily", scope_params)

    display_map = await _build_display_map()

    start = datetime.fromisoformat(f"{target_date}T00:00:00+00:00")
    end = start + timedelta(days=1)

    asyncio.create_task(
        _run_generation(
            briefing.id,
            retrieve_contents(start_time=start, end_time=end, limit=100),
            display_map=display_map,
        )
    )
    return briefing


async def generate_topic_briefing(
    keyword: str,
    hours: int = 72,
) -> Briefing:
    """Generate a briefing for a specific topic keyword within a time range."""
    title = f"主题简报 - {keyword}"
    scope_params = {"keyword": keyword, "hours": hours}

    briefing = await _create_briefing(title, "topic", scope_params)

    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)

    display_map = await _build_display_map()

    asyncio.create_task(
        _run_generation(
            briefing.id,
            retrieve_contents(keyword=keyword, start_time=start, end_time=end, limit=50),
            display_map=display_map,
        )
    )
    return briefing


async def generate_custom_briefing(
    item_ids: list[int],
    title: str | None = None,
) -> Briefing:
    """Generate a briefing for user-selected hot items."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    title = title or f"自选简报 - {now_str}"
    scope_params = {"item_ids": item_ids}

    briefing = await _create_briefing(title, "custom", scope_params)

    display_map = await _build_display_map()

    asyncio.create_task(
        _run_generation(
            briefing.id,
            retrieve_contents(item_ids=item_ids, limit=len(item_ids)),
            display_map=display_map,
        )
    )
    return briefing


async def find_duplicate_generating(
    brief_type: str,
    scope_params: dict,
) -> Briefing | None:
    """Find an existing generating briefing with the same type and scope."""
    async with async_session() as session:
        result = await session.execute(
            select(Briefing).where(
                Briefing.brief_type == brief_type,
                Briefing.status == "generating",
                Briefing.scope_params == scope_params,
            )
        )
        return result.scalar_one_or_none()
