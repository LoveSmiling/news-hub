"""Add pgvector extension and embedding column to hot_items

Revision ID: 004
Revises: 003
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # 1024-dim float vector for bge-m3 embeddings
    op.execute(
        "ALTER TABLE hot_items ADD COLUMN embedding vector(1024)"
    )
    # HNSW index for fast cosine similarity search
    op.execute(
        "CREATE INDEX idx_hot_items_embedding ON hot_items "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_hot_items_embedding")
    op.drop_column("hot_items", "embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
