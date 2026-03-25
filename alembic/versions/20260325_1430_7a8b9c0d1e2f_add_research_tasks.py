"""add research tasks table

Revision ID: 7a8b9c0d1e2f
Revises: 4d5e6f7a8b9c
Create Date: 2026-03-25 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision = "7a8b9c0d1e2f"
down_revision = "4d5e6f7a8b9c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_tasks",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("thread_id", sa.String(length=255), nullable=False),
        sa.Column("topic", sa.String(length=500), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", name="research_status"), nullable=False),
        sa.Column("max_analysts", sa.Integer(), nullable=True),
        sa.Column("max_turns", sa.Integer(), nullable=True),
        sa.Column("analysts_config", JSON(), nullable=True),
        sa.Column("final_report", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_research_tasks_id"), "research_tasks", ["id"], unique=False)
    op.create_index(op.f("ix_research_tasks_thread_id"), "research_tasks", ["thread_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_research_tasks_thread_id"), table_name="research_tasks")
    op.drop_index(op.f("ix_research_tasks_id"), table_name="research_tasks")
    op.drop_table("research_tasks")
