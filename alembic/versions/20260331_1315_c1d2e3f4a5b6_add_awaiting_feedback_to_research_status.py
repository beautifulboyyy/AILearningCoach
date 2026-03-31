"""add awaiting feedback to research status

Revision ID: c1d2e3f4a5b6
Revises: 7a8b9c0d1e2f
Create Date: 2026-03-31 13:15:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "c1d2e3f4a5b6"
down_revision = "7a8b9c0d1e2f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE research_status ADD VALUE IF NOT EXISTS 'AWAITING_FEEDBACK'"
    )


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in a simple downgrade.
    pass
