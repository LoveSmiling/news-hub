from datetime import datetime

from sqlalchemy import Computed, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class HotItem(Base):
    __tablename__ = "hot_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hot_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    embedding = mapped_column(Vector(1024), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Generated tsvector column for full-text search (managed by DB, read-only in ORM)
    title_tsv = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('simple', coalesce(title, ''))", persisted=True),
        nullable=True,
    )

    __table_args__ = (
        Index("idx_source_collected_at", "source", "collected_at"),
    )

    def __repr__(self) -> str:
        return f"<HotItem(source={self.source!r}, title={self.title!r})>"
