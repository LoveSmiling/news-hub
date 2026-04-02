"""Add summary and keywords columns to hot_items

Revision ID: 003
Revises: 002
Create Date: 2026-04-01
"""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("hot_items", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column(
        "hot_items",
        sa.Column("keywords", sa.dialects.postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("hot_items", "keywords")
    op.drop_column("hot_items", "summary")
