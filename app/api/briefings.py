"""Briefing API endpoints — list, detail, generate, delete, share."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, func, select

from app.db.database import async_session
from app.models.briefing import Briefing, BriefingItem
from app.models.hot_item import HotItem
from app.models.source import Source
from app.services.briefing_generator import (
    find_duplicate_generating,
    generate_custom_briefing,
    generate_daily_briefing,
    generate_source_briefing,
    generate_topic_briefing,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/briefings", tags=["briefings"])


# ── Schemas ───────────────────────────────────────────────────────

class BriefingSummary(BaseModel):
    id: int
    title: str
    brief_type: str
    status: str
    token_usage: int | None = None
    share_token: str | None = None
    share_expires: datetime | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class HotItemRef(BaseModel):
    id: int
    title: str
    source: str
    source_display_name: str = ""
    url: str

    model_config = {"from_attributes": True}


class BriefingDetail(BriefingSummary):
    content: str | None = None
    scope_params: dict | None = None
    items: list[HotItemRef] = []


class GenerateRequest(BaseModel):
    type: str  # source / daily / topic / custom
    source: str | None = None
    date: str | None = None
    keyword: str | None = None
    hours: int = 72
    item_ids: list[int] | None = None
    title: str | None = None


class BriefingListResponse(BaseModel):
    items: list[BriefingSummary]
    total: int


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("")
async def list_briefings(
    type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> BriefingListResponse:
    """Return paginated briefing list with optional type/status filtering."""
    async with async_session() as session:
        query = select(Briefing)

        if type:
            query = query.where(Briefing.brief_type == type)
        if status:
            query = query.where(Briefing.status == status)

        count_q = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_q)).scalar() or 0

        query = query.order_by(Briefing.created_at.desc()).offset(offset).limit(limit)
        result = await session.execute(query)
        rows = result.scalars().all()

    return BriefingListResponse(
        items=[BriefingSummary.model_validate(r) for r in rows],
        total=total,
    )


@router.get("/{briefing_id}")
async def get_briefing(briefing_id: int) -> BriefingDetail:
    """Return briefing detail with associated hot items."""
    async with async_session() as session:
        briefing = await session.get(Briefing, briefing_id)
        if not briefing:
            raise HTTPException(status_code=404, detail="Briefing not found")

        # Fetch associated hot items
        item_q = (
            select(HotItem.id, HotItem.title, HotItem.source, HotItem.url,
                   Source.display_name.label("source_display_name"))
            .join(BriefingItem, BriefingItem.hot_item_id == HotItem.id)
            .outerjoin(Source, Source.name == HotItem.source)
            .where(BriefingItem.briefing_id == briefing_id)
        )
        result = await session.execute(item_q)
        hot_items = [
            HotItemRef(
                id=r.id, title=r.title, source=r.source, url=r.url,
                source_display_name=r.source_display_name or r.source,
            )
            for r in result.all()
        ]

    detail = BriefingDetail.model_validate(briefing)
    detail.items = hot_items
    return detail


@router.post("/generate")
async def trigger_generate(req: GenerateRequest) -> BriefingSummary:
    """Trigger async briefing generation. Returns immediately."""
    # Build scope_params for duplicate check
    scope_map = {
        "source": {"source": req.source, "date": req.date},
        "daily": {"date": req.date},
        "topic": {"keyword": req.keyword, "hours": req.hours},
        "custom": {"item_ids": req.item_ids},
    }
    scope_params = scope_map.get(req.type)

    # Duplicate check
    if scope_params:
        dup = await find_duplicate_generating(req.type, scope_params)
        if dup:
            return BriefingSummary.model_validate(dup)

    if req.type == "source":
        if not req.source:
            raise HTTPException(400, "source is required for type=source")
        briefing = await generate_source_briefing(req.source, req.date)
    elif req.type == "daily":
        briefing = await generate_daily_briefing(req.date)
    elif req.type == "topic":
        if not req.keyword:
            raise HTTPException(400, "keyword is required for type=topic")
        briefing = await generate_topic_briefing(req.keyword, req.hours)
    elif req.type == "custom":
        if not req.item_ids:
            raise HTTPException(400, "item_ids is required for type=custom")
        briefing = await generate_custom_briefing(req.item_ids, req.title)
    else:
        raise HTTPException(400, f"Unknown briefing type: {req.type}")

    return BriefingSummary.model_validate(briefing)


@router.delete("/{briefing_id}")
async def delete_briefing(briefing_id: int):
    """Delete a briefing and its associated items."""
    async with async_session() as session:
        briefing = await session.get(Briefing, briefing_id)
        if not briefing:
            raise HTTPException(status_code=404, detail="Briefing not found")

        await session.execute(
            delete(BriefingItem).where(BriefingItem.briefing_id == briefing_id)
        )
        await session.delete(briefing)
        await session.commit()

    return {"ok": True}


# ── Share ─────────────────────────────────────────────────────────

_EXPIRES_MAP = {
    "1d": timedelta(days=1),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


class ShareRequest(BaseModel):
    expires_in: str | None = "7d"  # "1d" / "7d" / "30d" / null (permanent)


class ShareResponse(BaseModel):
    share_token: str
    share_url: str
    expires_at: datetime | None = None


@router.post("/{briefing_id}/share")
async def create_or_update_share(briefing_id: int, req: ShareRequest) -> ShareResponse:
    """Create a share link or update expiration for an existing share."""
    async with async_session() as session:
        briefing = await session.get(Briefing, briefing_id)
        if not briefing:
            raise HTTPException(404, "Briefing not found")
        if briefing.status != "done":
            raise HTTPException(400, "只能分享已完成的简报")

        # Calculate expiration
        if req.expires_in and req.expires_in in _EXPIRES_MAP:
            expires_at = datetime.now(timezone.utc) + _EXPIRES_MAP[req.expires_in]
        else:
            expires_at = None  # permanent

        if briefing.share_token:
            # Update expiration only, keep token
            briefing.share_expires = expires_at
        else:
            # Generate new token
            briefing.share_token = secrets.token_urlsafe(24)
            briefing.share_expires = expires_at

        await session.commit()
        await session.refresh(briefing)

    return ShareResponse(
        share_token=briefing.share_token,
        share_url=f"/share/{briefing.share_token}",
        expires_at=briefing.share_expires,
    )


@router.delete("/{briefing_id}/share")
async def cancel_share(briefing_id: int):
    """Cancel sharing — clears token and expiration."""
    async with async_session() as session:
        briefing = await session.get(Briefing, briefing_id)
        if not briefing:
            raise HTTPException(404, "Briefing not found")
        if not briefing.share_token:
            raise HTTPException(404, "此简报未分享")

        briefing.share_token = None
        briefing.share_expires = None
        await session.commit()

    return {"detail": "分享已取消"}
