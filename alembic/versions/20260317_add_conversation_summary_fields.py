"""add conversation summary fields

Revision ID: 3c4d5e6f7a8b
Revises: 2a3b4c5d6e7f
Create Date: 2026-03-17 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3c4d5e6f7a8b"
down_revision = "2a3b4c5d6e7f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("conversations", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("conversations", sa.Column("summary_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("conversations", "summary_updated_at")
    op.drop_column("conversations", "summary")
