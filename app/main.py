import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.hot import router as hot_router
from app.api.sources import router as sources_router
from app.api.search import router as search_router
from app.api.history import router as history_router
from app.api.ai import router as ai_router
from app.api.trends import router as trends_router
from app.api.recommend import router as recommend_router
from app.api.ai_config import router as ai_config_router
from app.api.logs import router as logs_router
from app.api.briefings import router as briefings_router
from app.api.chat import router as chat_router
from app.api.kb import router as kb_router
from app.api.share import router as share_router
from app.config import settings
from app.db.database import async_session
from app.models.source import Source
from app.models.hot_item import HotItem
from app.models.briefing import Briefing
from app.scheduler.jobs import scheduler, setup_scheduler
from app.services.collector import load_source_configs, collect_source

from sqlalchemy import select, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# New columns to add to sources table (name, type, default)
_NEW_COLUMNS = [
    ("type", "VARCHAR(20)", "'rsshub'"),
    ("route", "VARCHAR(200)", "''"),
    ("url", "VARCHAR(500)", "''"),
    ("schedule", "VARCHAR(50)", "'*/10 * * * *'"),
    ("max_items", "INTEGER", "30"),
]

# New columns to add to briefings table
_BRIEFING_NEW_COLUMNS = [
    ("share_token", "VARCHAR(32)", "NULL"),
    ("share_expires", "TIMESTAMP WITH TIME ZONE", "NULL"),
]


async def seed_sources():
    """Ensure all sources from sources.yaml exist in the database.

    Also handles schema migration: adds missing columns and backfills
    values from YAML for existing records (without overwriting user edits).
    """
    configs = load_source_configs()
    async with async_session() as session:
        # --- Auto-migrate: add missing columns ---
        for col_name, col_type, col_default in _NEW_COLUMNS:
            try:
                await session.execute(text(
                    f"ALTER TABLE sources ADD COLUMN {col_name} {col_type} DEFAULT {col_default}"
                ))
                logger.info("Added column sources.%s", col_name)
            except Exception:
                # Column already exists
                await session.rollback()
        await session.commit()

        # --- Seed & backfill ---
        for config in configs:
            result = await session.execute(
                select(Source).where(Source.name == config.name)
            )
            source = result.scalar_one_or_none()
            if not source:
                session.add(Source(
                    name=config.name,
                    display_name=config.display_name,
                    category=config.category,
                    type=config.type,
                    route=getattr(config, "route", ""),
                    url=getattr(config, "url", ""),
                    schedule=config.schedule,
                    max_items=config.max_items,
                    status="pending",
                ))
            else:
                # Backfill new fields only if they have default/empty values
                if not source.type or source.type == "rsshub":
                    source.type = config.type
                if not source.route:
                    source.route = getattr(config, "route", "")
                if not source.url:
                    source.url = getattr(config, "url", "")
                if not source.schedule or source.schedule == "*/10 * * * *":
                    source.schedule = config.schedule
                if not source.max_items or source.max_items == 30:
                    source.max_items = config.max_items
        await session.commit()
    logger.info("Seeded/backfilled %d sources", len(configs))


async def migrate_briefings():
    """Add missing columns to briefings table."""
    async with async_session() as session:
        for col_name, col_type, col_default in _BRIEFING_NEW_COLUMNS:
            try:
                await session.execute(text(
                    f"ALTER TABLE briefings ADD COLUMN {col_name} {col_type} DEFAULT {col_default}"
                ))
                logger.info("Added column briefings.%s", col_name)
            except Exception:
                await session.rollback()
        # Add unique index on share_token if not exists
        try:
            await session.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_briefings_share_token ON briefings (share_token)"
            ))
        except Exception:
            await session.rollback()
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting NewsHub...")
    await seed_sources()
    await migrate_briefings()
    await setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))
    yield
    # Shutdown
    scheduler.shutdown()
    logger.info("Scheduler shut down")


app = FastAPI(
    title="NewsHub API",
    description="多源热点信息聚合系统",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hot_router)
app.include_router(sources_router)
app.include_router(search_router)
app.include_router(history_router)
app.include_router(ai_router)
app.include_router(trends_router)
app.include_router(recommend_router)
app.include_router(ai_config_router)
app.include_router(logs_router)
app.include_router(briefings_router)
app.include_router(chat_router)
app.include_router(kb_router)
app.include_router(share_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/collect")
async def trigger_collect():
    """Manually trigger collection for all sources."""
    configs = load_source_configs()
    results = {}
    for config in configs:
        try:
            count = await collect_source(config.name)
            results[config.name] = {"status": "ok", "items": count}
        except Exception as e:
            results[config.name] = {"status": "error", "message": str(e)}
    return results


@app.post("/api/enrich-keywords")
async def trigger_enrich_keywords(
    limit: int = 50,
):
    """Manually trigger AI keyword extraction for items that lack keywords."""
    from app.services.ai.keyword_extractor import extract_keywords

    async with async_session() as session:
        result = await session.execute(
            select(HotItem)
            .where(HotItem.keywords.is_(None))
            .order_by(HotItem.collected_at.desc())
            .limit(limit)
        )
        items = result.scalars().all()

        success = 0
        errors = 0
        for item in items:
            try:
                kw = await extract_keywords(item.title)
                item.keywords = kw
                success += 1
            except Exception:
                errors += 1
                logger.debug("Keyword extraction failed for item %d", item.id)

        await session.commit()

    return {"total": len(items), "success": success, "errors": errors}


@app.post("/api/test-content-service")
async def test_content_service(
    source: str = "thepaper",
    limit: int = 5,
):
    """Test endpoint: retrieve cleaned content and optionally run Map-Reduce."""
    from app.services.content_service import retrieve_contents

    items = await retrieve_contents(source=source, limit=limit)
    return {
        "count": len(items),
        "items": [
            {
                "id": it.id,
                "title": it.title,
                "source": it.source,
                "content_preview": it.content[:300] if it.content else "",
                "content_length": len(it.content),
            }
            for it in items
        ],
    }


@app.post("/api/test-map-reduce")
async def test_map_reduce(
    source: str = "thepaper",
    limit: int = 10,
):
    """Test endpoint: run Map-Reduce summarization on recent items."""
    from app.services.content_service import retrieve_contents
    from app.services.ai.map_reduce_summarizer import map_reduce_summarize

    items = await retrieve_contents(source=source, limit=limit)
    if not items:
        return {"error": "No items found", "briefing": ""}

    briefing = await map_reduce_summarize(items)
    return {
        "source": source,
        "item_count": len(items),
        "briefing": briefing,
    }
