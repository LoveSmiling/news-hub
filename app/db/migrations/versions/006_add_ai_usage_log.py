"""add ai_usage_logs table

Revision ID: 006
Revises: 005
Create Date: 2026-03-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_usage_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("action", sa.String(50), nullable=False),  # keyword_extract, summarize, embedding, trend_generate
        sa.Column("provider_type", sa.String(20), nullable=False),  # llm, embedding
        sa.Column("provider_name", sa.String(100), nullable=True),  # config name
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("meta", postgresql.JSONB(), nullable=True),  # extra context: source, item_id, etc.
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_usage_logs_action", "ai_usage_logs", ["action"])
    op.create_index("idx_ai_usage_logs_created_at", "ai_usage_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_ai_usage_logs_created_at")
    op.drop_index("idx_ai_usage_logs_action")
    op.drop_table("ai_usage_logs")
