import time
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.models.source import Source
from app.models.hot_item import HotItem
from app.api.schemas import (
    SourceResponse, SourceCreate, SourceUpdate,
    SourceTestRequest, SourceTestResponse,
    BatchActionRequest,
    SourceExportItem, SourceExportResponse,
    SourceImportRequest, SourceImportResponse, SourceImportError,
)
from app.scheduler.jobs import register_source_job, remove_source_job
from app.services.collector import collect_source, create_spider, _source_to_config
from app.spiders.base import SourceConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("/categories", response_model=list[str])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get distinct category list."""
    result = await db.execute(
        select(Source.category).distinct().order_by(Source.category)
    )
    return [row[0] for row in result.all()]


@router.get("", response_model=list[SourceResponse])
async def get_sources(db: AsyncSession = Depends(get_db)):
    """Get all configured data sources with their status."""
    result = await db.execute(select(Source).order_by(Source.category, Source.name))
    sources = result.scalars().all()
    return [SourceResponse.model_validate(s) for s in sources]


@router.get("/export")
async def export_sources(db: AsyncSession = Depends(get_db)):
    """Export all sources as a downloadable JSON file."""
    result = await db.execute(select(Source).order_by(Source.category, Source.name))
    sources = result.scalars().all()

    export_data = SourceExportResponse(
        version=1,
        exported_at=datetime.now(timezone.utc).isoformat(),
        sources=[SourceExportItem.model_validate(s) for s in sources],
    )

    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return JSONResponse(
        content=export_data.model_dump(),
        headers={
            "Content-Disposition": f'attachment; filename="sources_export_{today}.json"',
        },
    )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single source by ID."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceResponse.model_validate(source)


@router.post("", response_model=SourceResponse, status_code=201)
async def create_source(body: SourceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new source."""
    # Check uniqueness
    existing = await db.execute(select(Source).where(Source.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Source name already exists")

    source = Source(
        name=body.name,
        display_name=body.display_name,
        category=body.category,
        type=body.type,
        route=body.route,
        url=body.url,
        schedule=body.schedule,
        max_items=body.max_items,
        status="pending",
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    # Register scheduler job
    register_source_job(source)

    return SourceResponse.model_validate(source)


@router.post("/import", response_model=SourceImportResponse)
async def import_sources(body: SourceImportRequest, db: AsyncSession = Depends(get_db)):
    """Import sources from JSON: update existing (by name) or create new."""
    created = 0
    updated = 0
    errors: list[SourceImportError] = []

    for item in body.sources:
        try:
            result = await db.execute(select(Source).where(Source.name == item.name))
            existing = result.scalar_one_or_none()

            if existing:
                old_schedule = existing.schedule
                old_status = existing.status
                existing.display_name = item.display_name
                existing.category = item.category
                existing.type = item.type
                existing.route = item.route
                existing.url = item.url
                existing.schedule = item.schedule
                existing.max_items = item.max_items
                existing.status = item.status
                updated += 1

                # Sync scheduler if schedule or status changed
                if item.status == "disabled":
                    remove_source_job(existing.name)
                elif old_schedule != item.schedule or old_status != item.status:
                    register_source_job(existing)
            else:
                source = Source(
                    name=item.name,
                    display_name=item.display_name,
                    category=item.category,
                    type=item.type,
                    route=item.route,
                    url=item.url,
                    schedule=item.schedule,
                    max_items=item.max_items,
                    status=item.status,
                )
                db.add(source)
                created += 1

                # Register scheduler for new active sources
                if item.status == "active":
                    await db.flush()
                    register_source_job(source)
        except Exception as e:
            errors.append(SourceImportError(name=item.name, error=str(e)))

    await db.commit()
    return SourceImportResponse(created=created, updated=updated, errors=errors)


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(source_id: int, body: SourceUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing source."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(source, key, value)

    await db.commit()
    await db.refresh(source)

    # Update scheduler job
    if source.status != "disabled":
        register_source_job(source)
    else:
        remove_source_job(source.name)

    return SourceResponse.model_validate(source)


@router.delete("/{source_id}")
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a source. Soft-delete (disabled) for sources with data, hard-delete for pending+no data."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Remove scheduler job
    remove_source_job(source.name)

    # Check if physical delete is safe
    if source.status == "pending":
        item_count = await db.execute(
            select(func.count()).select_from(HotItem).where(HotItem.source == source.name)
        )
        if item_count.scalar() == 0:
            await db.delete(source)
            await db.commit()
            return {"detail": "Source permanently deleted"}

    # Soft delete
    source.status = "disabled"
    await db.commit()
    return {"detail": "Source disabled"}


@router.post("/test", response_model=SourceTestResponse)
async def test_source(body: SourceTestRequest):
    """Test/preview a source configuration without saving to DB."""
    config = SourceConfig(
        name="__test__",
        display_name="Test",
        category="test",
        type=body.type,
        route=body.route,
        url=body.url,
        schedule="*/10 * * * *",
        max_items=body.max_items,
    )

    start = time.time()
    try:
        spider = create_spider(config, settings.rsshub_url)
        items = await spider.fetch()
        elapsed = int((time.time() - start) * 1000)
        return SourceTestResponse(
            success=True,
            items=[{"title": it.title, "url": it.url, "rank": it.rank} for it in items],
            count=len(items),
            elapsed_ms=elapsed,
        )
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return SourceTestResponse(
            success=False,
            error=str(e),
            elapsed_ms=elapsed,
        )


@router.post("/{source_id}/collect")
async def collect_source_now(source_id: int, db: AsyncSession = Depends(get_db)):
    """Trigger immediate collection for a source."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status == "disabled":
        raise HTTPException(status_code=400, detail="Source is disabled")

    count = await collect_source(source.name)
    return {"detail": f"Collected {count} items", "count": count}


@router.patch("/batch")
async def batch_action(body: BatchActionRequest, db: AsyncSession = Depends(get_db)):
    """Perform batch operations on multiple sources."""
    result = await db.execute(select(Source).where(Source.id.in_(body.ids)))
    sources = result.scalars().all()

    if not sources:
        raise HTTPException(status_code=404, detail="No sources found for given IDs")

    results = {}

    if body.action == "enable":
        for s in sources:
            s.status = "active"
            register_source_job(s)
            results[s.name] = "enabled"

    elif body.action == "disable":
        for s in sources:
            s.status = "disabled"
            remove_source_job(s.name)
            results[s.name] = "disabled"

    elif body.action == "set_category":
        if not body.category:
            raise HTTPException(status_code=400, detail="category is required for set_category action")
        for s in sources:
            s.category = body.category
            results[s.name] = f"category set to {body.category}"

    elif body.action == "collect":
        await db.commit()  # commit any pending changes first
        for s in sources:
            if s.status == "disabled":
                results[s.name] = "skipped (disabled)"
                continue
            try:
                count = await collect_source(s.name)
                results[s.name] = f"collected {count} items"
            except Exception as e:
                results[s.name] = f"error: {e}"
        return {"detail": "Batch collect completed", "results": results}

    await db.commit()
    return {"detail": f"Batch {body.action} completed", "results": results}
