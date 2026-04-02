"""Add ai_config table for dynamic LLM/Embedding provider configuration

Revision ID: 005
Revises: 004
Create Date: 2026-03-31
"""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_configs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column(
            "provider_type",
            sa.String(20),
            nullable=False,
            comment="llm or embedding",
        ),
        sa.Column("api_base", sa.Text, nullable=False),
        sa.Column("api_key", sa.String(200), nullable=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "extra",
            sa.dialects.postgresql.JSONB,
            nullable=True,
            comment="Extra params like temperature, max_tokens, embed_dim",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("idx_ai_configs_type_default", "ai_configs", ["provider_type", "is_default"])


def downgrade() -> None:
    op.drop_index("idx_ai_configs_type_default")
    op.drop_table("ai_configs")
