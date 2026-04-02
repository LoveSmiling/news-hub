from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.hot_item import HotItem
from app.api.schemas import SummaryResponse
from app.services.ai.summarizer import summarize_single
from app.services.ai.keyword_extractor import extract_keywords

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/summary/{item_id}", response_model=SummaryResponse)
async def generate_summary(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate an AI summary for a specific hot item on demand."""
    result = await db.execute(select(HotItem).where(HotItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.summary:
        return SummaryResponse(id=item.id, summary=item.summary)

    summary = await summarize_single(item.title)
    item.summary = summary
    await db.commit()
    return SummaryResponse(id=item.id, summary=summary)


@router.post("/keywords/{item_id}")
async def generate_keywords(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate AI keywords for a specific hot item on demand."""
    result = await db.execute(select(HotItem).where(HotItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.keywords:
        return {"id": item.id, "keywords": item.keywords}

    keywords = await extract_keywords(item.title)
    item.keywords = keywords
    await db.commit()
    return {"id": item.id, "keywords": keywords}
