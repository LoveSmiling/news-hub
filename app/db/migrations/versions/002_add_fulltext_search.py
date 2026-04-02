"""Add fulltext search tsvector column and GIN index

Revision ID: 002
Revises: 001
Create Date: 2026-03-31
"""

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add tsvector column for full-text search
    op.execute(
        """
        ALTER TABLE hot_items
        ADD COLUMN title_tsv tsvector
        GENERATED ALWAYS AS (
            to_tsvector('simple', coalesce(title, ''))
        ) STORED
        """
    )
    # Create GIN index on the tsvector column
    op.execute(
        "CREATE INDEX idx_hot_items_title_tsv ON hot_items USING GIN (title_tsv)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_hot_items_title_tsv")
    op.execute("ALTER TABLE hot_items DROP COLUMN IF EXISTS title_tsv")
