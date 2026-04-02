"""Knowledge base service — embedding text building and batch generation."""

from __future__ import annotations

import logging

from sqlalchemy import select, update

from app.db.database import async_session
from app.models.hot_item import HotItem
from app.services.ai.embedder import get_embeddings_batch
from app.utils.html_cleaner import clean_html, truncate_text

logger = logging.getLogger(__name__)

EMBED_TEXT_MAX_CHARS = 500
BATCH_SIZE = 50


def build_embedding_text(title: str, raw_summary: str | None) -> str:
    """Build the text used for embedding generation.

    Combines title (higher weight at start) with cleaned summary.
    """
    summary = truncate_text(clean_html(raw_summary or ""), EMBED_TEXT_MAX_CHARS)
    return f"{title}\n\n{summary}" if summary else title


async def batch_generate_embeddings(
    item_ids: list[int] | None = None,
    batch_size: int = BATCH_SIZE,
    progress_callback=None,
) -> dict:
    """Generate embeddings for hot_items that lack them.

    Args:
        item_ids: Specific item IDs to process. If None, processes all with embedding IS NULL.
        batch_size: Number of items per batch.
        progress_callback: Optional async callable(processed_count) for progress updates.

    Returns:
        Dict with success/error counts.
    """
    total_success = 0
    total_errors = 0
    processed = 0
    max_consecutive_errors = 3
    consecutive_errors = 0

    while True:
        async with async_session() as session:
            query = (
                select(
                    HotItem.id,
                    HotItem.title,
                    HotItem.raw_data["summary"].as_string().label("raw_summary"),
                )
                .where(HotItem.embedding.is_(None))
            )
            if item_ids is not None:
                query = query.where(HotItem.id.in_(item_ids))

            query = query.order_by(HotItem.id).limit(batch_size)
            result = await session.execute(query)
            rows = result.all()

        if not rows:
            break

        texts = [build_embedding_text(r.title, r.raw_summary) for r in rows]
        ids = [r.id for r in rows]

        try:
            embeddings = await get_embeddings_batch(
                texts, log_meta={"action": "kb_batch"}
            )

            async with async_session() as session:
                for item_id, emb in zip(ids, embeddings):
                    await session.execute(
                        update(HotItem)
                        .where(HotItem.id == item_id)
                        .values(embedding=emb)
                    )
                await session.commit()

            total_success += len(rows)
            consecutive_errors = 0
        except Exception:
            logger.error("Batch embedding failed for %d items", len(rows), exc_info=True)
            total_errors += len(rows)
            consecutive_errors += 1
            # For specific item_ids, remove failed ones to avoid retrying
            if item_ids is not None:
                item_ids = [i for i in item_ids if i not in ids]

            if consecutive_errors >= max_consecutive_errors:
                logger.error("Too many consecutive errors (%d), aborting task", consecutive_errors)
                break

        processed += len(rows)
        if progress_callback:
            await progress_callback(processed)

    return {"success": total_success, "errors": total_errors}
