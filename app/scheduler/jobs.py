import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.services.collector import collect_source

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def daily_briefing_job() -> None:
    """Generate daily briefings: one per active source + a cross-source summary.

    Runs serially to avoid overloading the LLM service.  Partial failures
    are logged and do not abort the remaining sources.
    """
    from app.services.briefing_generator import (
        generate_source_briefing,
        generate_daily_briefing,
    )
    import asyncio
    from sqlalchemy import select
    from app.db.database import async_session
    from app.models.source import Source

    async with async_session() as session:
        result = await session.execute(
            select(Source).where(Source.status != "disabled")
        )
        sources = result.scalars().all()

    logger.info("Daily briefing job started for %d sources", len(sources))

    for source in sources:
        try:
            briefing = await generate_source_briefing(source.name)
            await asyncio.sleep(0)
            from app.models.briefing import Briefing
            for _ in range(60):
                await asyncio.sleep(5)
                async with async_session() as session:
                    b = await session.get(Briefing, briefing.id)
                    if b and b.status in ("done", "failed"):
                        break
            logger.info("Source briefing %s: status=%s", source.name, b.status if b else "?")
        except Exception:
            logger.error("Failed to generate briefing for %s", source.name, exc_info=True)

    # Cross-source daily summary
    try:
        briefing = await generate_daily_briefing()
        logger.info("Daily summary briefing created: id=%d", briefing.id)
    except Exception:
        logger.error("Failed to generate daily summary briefing", exc_info=True)


def register_source_job(source) -> None:
    """Register or update a scheduler job for a source (from DB model)."""
    try:
        trigger = CronTrigger.from_crontab(source.schedule)
    except ValueError:
        logger.error("Invalid cron expression for %s: %s", source.name, source.schedule)
        return

    scheduler.add_job(
        collect_source,
        trigger=trigger,
        args=[source.name],
        id=f"collect_{source.name}",
        name=f"Collect {source.display_name}",
        replace_existing=True,
        misfire_grace_time=60,
    )
    logger.info("Registered job: collect_%s (%s)", source.name, source.schedule)


def remove_source_job(source_name: str) -> None:
    """Remove a scheduler job for a source."""
    job_id = f"collect_{source_name}"
    try:
        scheduler.remove_job(job_id)
        logger.info("Removed job: %s", job_id)
    except Exception:
        logger.debug("Job %s not found, skip removal", job_id)


async def setup_scheduler() -> AsyncIOScheduler:
    """Load sources from DB and register collection jobs."""
    from sqlalchemy import select
    from app.db.database import async_session
    from app.models.source import Source

    async with async_session() as session:
        result = await session.execute(
            select(Source).where(Source.status != "disabled")
        )
        sources = result.scalars().all()

    for source in sources:
        register_source_job(source)

    # Daily briefing job at 23:00
    scheduler.add_job(
        daily_briefing_job,
        trigger=CronTrigger(hour=23, minute=0),
        id="daily_briefing",
        name="Daily Briefing Generation",
        replace_existing=True,
        misfire_grace_time=300,
    )
    logger.info("Registered job: daily_briefing (23:00)")

    return scheduler
