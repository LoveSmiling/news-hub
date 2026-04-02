"""add briefings and briefing_items tables

Revision ID: 007
Revises: 006
Create Date: 2026-04-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "briefings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("brief_type", sa.String(20), nullable=False),
        sa.Column("scope_params", postgresql.JSONB(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("token_usage", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_briefings_brief_type", "briefings", ["brief_type"])
    op.create_index("idx_briefings_status", "briefings", ["status"])
    op.create_index("idx_briefings_created_at", "briefings", ["created_at"])

    op.create_table(
        "briefing_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("briefing_id", sa.Integer(), nullable=False),
        sa.Column("hot_item_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["briefing_id"], ["briefings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hot_item_id"], ["hot_items.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_briefing_items_briefing_id", "briefing_items", ["briefing_id"])
    op.create_index("idx_briefing_items_hot_item_id", "briefing_items", ["hot_item_id"])


def downgrade() -> None:
    op.drop_index("idx_briefing_items_hot_item_id")
    op.drop_index("idx_briefing_items_briefing_id")
    op.drop_table("briefing_items")
    op.drop_index("idx_briefings_created_at")
    op.drop_index("idx_briefings_status")
    op.drop_index("idx_briefings_brief_type")
    op.drop_table("briefings")
