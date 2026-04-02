"""Knowledge base task manager — in-memory async task execution with progress tracking."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import update

from app.db.database import async_session
from app.models.hot_item import HotItem
from app.services.kb_service import batch_generate_embeddings

logger = logging.getLogger(__name__)

TaskType = Literal["incremental", "full_rebuild"]
TaskStatus = Literal["pending", "running", "done", "failed"]


@dataclass
class KBTask:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    type: TaskType = "incremental"
    status: TaskStatus = "pending"
    progress: int = 0
    total: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.id,
            "type": self.type,
            "status": self.status,
            "progress": self.progress,
            "total": self.total,
            "created_at": self.created_at.isoformat(),
            "error": self.error,
        }


# In-memory task storage
_tasks: dict[str, KBTask] = {}


def get_task(task_id: str) -> KBTask | None:
    return _tasks.get(task_id)


def has_running_task() -> bool:
    return any(t.status in ("pending", "running") for t in _tasks.values())


async def _count_unindexed() -> int:
    """Count hot_items without embedding."""
    from sqlalchemy import func, select

    async with async_session() as session:
        result = await session.execute(
            select(func.count(HotItem.id)).where(HotItem.embedding.is_(None))
        )
        return result.scalar() or 0


async def _count_all() -> int:
    """Count all hot_items."""
    from sqlalchemy import func, select

    async with async_session() as session:
        result = await session.execute(select(func.count(HotItem.id)))
        return result.scalar() or 0


async def create_task(task_type: TaskType) -> KBTask:
    """Create and launch a background KB task."""
    if has_running_task():
        raise RuntimeError("已有任务正在运行")

    task = KBTask(type=task_type)

    if task_type == "full_rebuild":
        # Clear all embeddings first
        async with async_session() as session:
            await session.execute(
                update(HotItem).values(embedding=None)
            )
            await session.commit()
        task.total = await _count_all()
    else:
        task.total = await _count_unindexed()

    _tasks[task.id] = task

    # Launch background processing
    asyncio.create_task(_run_task(task))
    return task


async def _run_task(task: KBTask) -> None:
    """Execute the embedding generation task."""
    task.status = "running"
    logger.info("KB task %s (%s) started: %d items", task.id, task.type, task.total)

    try:

        async def on_progress(processed: int):
            task.progress = processed

        result = await batch_generate_embeddings(
            progress_callback=on_progress,
        )

        task.progress = task.total
        task.status = "done"
        logger.info(
            "KB task %s done: %d success, %d errors",
            task.id,
            result["success"],
            result["errors"],
        )

    except Exception as e:
        task.status = "failed"
        task.error = str(e)[:500]
        logger.error("KB task %s failed", task.id, exc_info=True)
