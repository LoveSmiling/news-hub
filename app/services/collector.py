import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import async_session
from app.models.hot_item import HotItem
from app.models.source import Source
from app.spiders.base import SourceConfig, SpiderItem
from app.spiders.rss_spider import RSSSpider

logger = logging.getLogger(__name__)

SOURCES_YAML = Path(__file__).parent.parent / "spiders" / "sources.yaml"


def load_source_configs() -> list[SourceConfig]:
    """Load source configurations from sources.yaml (used for seeding only)."""
    with open(SOURCES_YAML, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    sources = []
    for item in data.get("sources", []):
        sources.append(SourceConfig(**item))
    return sources


def _source_to_config(source: Source) -> SourceConfig:
    """Convert a DB Source model to a SourceConfig dataclass."""
    return SourceConfig(
        name=source.name,
        display_name=source.display_name,
        category=source.category,
        type=source.type or "rsshub",
        route=source.route or "",
        url=source.url or "",
        schedule=source.schedule or "*/10 * * * *",
        max_items=source.max_items or 30,
    )


def create_spider(config: SourceConfig, rsshub_url: str):
    """Create the appropriate spider based on source type."""
    if config.type in ("rsshub", "rss"):
        return RSSSpider(config, rsshub_url)
    raise ValueError(f"Unknown spider type: {config.type}")


async def collect_source(source_name: str) -> int:
    """Collect data from a single source (by name) and save to database.

    Reads full configuration from DB. Returns the number of new/updated items.
    """
    async with async_session() as session:
        result = await session.execute(
            select(Source).where(Source.name == source_name)
        )
        source = result.scalar_one_or_none()

    if not source:
        logger.error("Source %s not found in DB, skipping collection", source_name)
        return 0

    source_config = _source_to_config(source)
    spider = create_spider(source_config, settings.rsshub_url)

    try:
        items = await spider.fetch()
    except Exception:
        logger.exception("Error fetching source %s", source_config.name)
        return 0

    if not items:
        logger.warning("No items fetched for %s", source_name)
        return 0

    collected_at = datetime.now(timezone.utc)
    count = 0

    async with async_session() as session:
        count = await _save_items(session, source_config, items, collected_at)
        await _update_source_status(session, source_name, collected_at)
        await session.commit()

    # Generate AI keywords for new items (best-effort, non-blocking failures)
    if count > 0:
        try:
            await _enrich_ai_keywords(source_name, collected_at)
        except Exception:
            logger.warning("AI keyword enrichment failed for %s, skipping", source_name)

        try:
            await _enrich_embeddings(source_name, collected_at)
        except Exception:
            logger.warning("Embedding enrichment failed for %s, skipping", source_name)

    logger.info("Saved %d items for %s", count, source_name)
    return count


async def _save_items(
    session: AsyncSession,
    config: SourceConfig,
    items: list[SpiderItem],
    collected_at: datetime,
) -> int:
    """Save spider items to database with dedup logic."""
    count = 0

    for item in items:
        # Check for existing item by source + url in last 24 hours
        existing = await session.execute(
            select(HotItem).where(
                and_(
                    HotItem.source == config.name,
                    HotItem.url == item.url,
                    HotItem.collected_at >= collected_at.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ),
                )
            )
        )
        existing_item = existing.scalar_one_or_none()

        if existing_item:
            # Update rank and hot_value if changed
            existing_item.rank = item.rank
            existing_item.hot_value = item.hot_value
            existing_item.collected_at = collected_at
        else:
            new_item = HotItem(
                source=config.name,
                title=item.title,
                url=item.url,
                rank=item.rank,
                hot_value=item.hot_value,
                category=config.category,
                raw_data=item.raw_data,
                collected_at=collected_at,
            )
            session.add(new_item)
            count += 1

    return count


async def _update_source_status(
    session: AsyncSession,
    source_name: str,
    collected_at: datetime,
) -> None:
    """Update the source record with last collection time."""
    result = await session.execute(
        select(Source).where(Source.name == source_name)
    )
    source = result.scalar_one_or_none()

    if source:
        source.last_collected_at = collected_at
        source.status = "active"


async def _enrich_ai_keywords(source_name: str, collected_at: datetime) -> None:
    """Enrich newly collected items with AI-generated keywords."""
    from app.services.ai.keyword_extractor import extract_keywords

    async with async_session() as session:
        result = await session.execute(
            select(HotItem)
            .where(
                and_(
                    HotItem.source == source_name,
                    HotItem.collected_at == collected_at,
                    HotItem.keywords.is_(None),
                )
            )
            .order_by(HotItem.rank.asc().nullslast())
        )
        items = result.scalars().all()

        for item in items:
            try:
                kw = await extract_keywords(item.title)
                item.keywords = kw
            except Exception:
                logger.debug("Keyword extraction failed for item %d", item.id)

        await session.commit()


async def _enrich_embeddings(source_name: str, collected_at: datetime) -> None:
    """Generate embeddings for newly collected items that don't have them yet."""
    from app.services.ai.llm_client import get_embeddings_batch
    from app.services.kb_service import build_embedding_text

    async with async_session() as session:
        result = await session.execute(
            select(HotItem)
            .where(
                and_(
                    HotItem.source == source_name,
                    HotItem.collected_at == collected_at,
                    HotItem.embedding.is_(None),
                )
            )
        )
        items = result.scalars().all()

        if not items:
            return

        texts = [build_embedding_text(item.title, item.summary) for item in items]
        try:
            embeddings = await get_embeddings_batch(texts)
            for item, emb in zip(items, embeddings):
                item.embedding = emb
            await session.commit()
            logger.info("Generated embeddings for %d items from %s", len(items), source_name)
        except Exception:
            logger.warning("Embedding generation failed for %s batch", source_name)
            await session.rollback()
