"""Public share endpoint — view shared briefing by token."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.db.database import async_session
from app.models.briefing import Briefing, BriefingItem
from app.models.hot_item import HotItem
from app.models.source import Source

router = APIRouter(prefix="/api/share", tags=["share"])


class SharedHotItemRef(BaseModel):
    id: int
    title: str
    source: str
    source_display_name: str = ""
    url: str

    model_config = {"from_attributes": True}


class SharedBriefingResponse(BaseModel):
    title: str
    brief_type: str
    content: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    items: list[SharedHotItemRef] = []


@router.get("/{token}")
async def get_shared_briefing(token: str) -> SharedBriefingResponse:
    """Public endpoint to view a shared briefing by token."""
    async with async_session() as session:
        result = await session.execute(
            select(Briefing).where(Briefing.share_token == token)
        )
        briefing = result.scalar_one_or_none()

        if not briefing:
            raise HTTPException(404, "分享链接无效")

        # Check expiration
        if briefing.share_expires and briefing.share_expires <= datetime.now(timezone.utc):
            raise HTTPException(410, "分享链接已过期")

        # Fetch associated hot items
        item_q = (
            select(HotItem.id, HotItem.title, HotItem.source, HotItem.url,
                   Source.display_name.label("source_display_name"))
            .join(BriefingItem, BriefingItem.hot_item_id == HotItem.id)
            .outerjoin(Source, Source.name == HotItem.source)
            .where(BriefingItem.briefing_id == briefing.id)
        )
        item_result = await session.execute(item_q)
        hot_items = [
            SharedHotItemRef(
                id=r.id, title=r.title, source=r.source, url=r.url,
                source_display_name=r.source_display_name or r.source,
            )
            for r in item_result.all()
        ]

    return SharedBriefingResponse(
        title=briefing.title,
        brief_type=briefing.brief_type,
        content=briefing.content,
        created_at=briefing.created_at,
        completed_at=briefing.completed_at,
        items=hot_items,
    )
