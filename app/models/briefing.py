from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.database import Base


class Briefing(Base):
    __tablename__ = "briefings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    brief_type: Mapped[str] = mapped_column(String(20), nullable=False)  # source/daily/topic/custom
    scope_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_usage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    share_token: Mapped[str | None] = mapped_column(
        String(32), nullable=True, unique=True, index=True
    )
    share_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Briefing(id={self.id}, title={self.title!r}, status={self.status!r})>"


class BriefingItem(Base):
    __tablename__ = "briefing_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    briefing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("briefings.id", ondelete="CASCADE"), nullable=False
    )
    hot_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hot_items.id", ondelete="CASCADE"), nullable=False
    )
