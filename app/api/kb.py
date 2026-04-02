"""Knowledge base API — stats, semantic search, and task management."""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select

from app.db.database import async_session
from app.models.hot_item import HotItem
from app.services.ai.embedder import get_embedding
from app.services.kb_task_manager import create_task, get_task, has_running_task
from app.utils.html_cleaner import clean_html, truncate_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kb", tags=["knowledge-base"])


# ── Schemas ───────────────────────────────────────────────────────


class SourceStat(BaseModel):
    source: str
    total: int
    indexed: int


class KBStats(BaseModel):
    total: int
    indexed: int
    coverage_pct: float
    by_source: list[SourceStat]


class SearchRequest(BaseModel):
    query: str
    limit: int = 20


class SearchResultItem(BaseModel):
    id: int
    title: str
    source: str
    url: str
    summary: str
    score: float
    has_embedding: bool
    keywords: list[str] | None
    collected_at: str


class SearchResponse(BaseModel):
    items: list[SearchResultItem]


class TaskCreateRequest(BaseModel):
    type: Literal["incremental", "full_rebuild"]


class TaskResponse(BaseModel):
    task_id: str
    type: str
    status: str
    progress: int
    total: int
    created_at: str
    error: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────


@router.get("/stats", response_model=KBStats)
async def get_stats():
    """Get knowledge base statistics."""
    async with async_session() as session:
        # Total and indexed counts
        total = (await session.execute(select(func.count(HotItem.id)))).scalar() or 0
        indexed = (
            await session.execute(
                select(func.count(HotItem.id)).where(HotItem.embedding.isnot(None))
            )
        ).scalar() or 0

        # Per-source breakdown
        result = await session.execute(
            select(
                HotItem.source,
                func.count(HotItem.id).label("total"),
                func.count(HotItem.embedding).label("indexed"),
            ).group_by(HotItem.source)
        )
        by_source = [
            SourceStat(source=r.source, total=r.total, indexed=r.indexed)
            for r in result.all()
        ]

    coverage = round(indexed / total * 100, 1) if total > 0 else 0.0
    return KBStats(total=total, indexed=indexed, coverage_pct=coverage, by_source=by_source)


@router.post("/search", response_model=SearchResponse)
async def semantic_search(body: SearchRequest):
    """Search knowledge base using vector similarity."""
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        query_embedding = await get_embedding(query, log_meta={"action": "kb_search"})
    except Exception:
        logger.error("Failed to generate query embedding", exc_info=True)
        raise HTTPException(status_code=500, detail="Embedding generation failed")

    async with async_session() as session:
        # cosine_distance returns 0..2, convert to similarity score 0..1
        dist = HotItem.embedding.cosine_distance(query_embedding)
        result = await session.execute(
            select(
                HotItem.id,
                HotItem.title,
                HotItem.source,
                HotItem.url,
                HotItem.raw_data["summary"].as_string().label("raw_summary"),
                HotItem.keywords,
                HotItem.collected_at,
                dist.label("distance"),
            )
            .where(HotItem.embedding.isnot(None))
            .order_by(dist)
            .limit(body.limit)
        )
        rows = result.all()

    items = [
        SearchResultItem(
            id=r.id,
            title=r.title,
            source=r.source,
            url=r.url,
            summary=truncate_text(clean_html(r.raw_summary or ""), 200),
            score=round(1 - r.distance, 4),
            has_embedding=True,
            keywords=r.keywords,
            collected_at=r.collected_at.isoformat(),
        )
        for r in rows
    ]
    return SearchResponse(items=items)


@router.post("/tasks", response_model=TaskResponse, status_code=202)
async def create_kb_task(body: TaskCreateRequest):
    """Create a background KB building task."""
    if has_running_task():
        raise HTTPException(status_code=409, detail="已有任务正在运行")

    try:
        task = await create_task(body.type)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return TaskResponse(**task.to_dict())


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_kb_task(task_id: str):
    """Get task progress."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task.to_dict())
