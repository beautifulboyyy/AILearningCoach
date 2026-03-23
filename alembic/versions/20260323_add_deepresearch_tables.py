"""add deepresearch tables

Revision ID: 7e8f9a0b1c2d
Revises: 4d5e6f7a8b9c
Create Date: 2026-03-23 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7e8f9a0b1c2d"
down_revision = "4d5e6f7a8b9c"
branch_labels = None
depends_on = None


deep_research_task_status = sa.Enum(
    "PENDING",
    "DRAFTING_ANALYSTS",
    "WAITING_FEEDBACK",
    "RUNNING_RESEARCH",
    "COMPLETED",
    "FAILED",
    name="deepresearchtaskstatus",
)

deep_research_phase = sa.Enum(
    "ANALYST_GENERATION",
    "ANALYST_FEEDBACK",
    "RESEARCH_EXECUTION",
    "REPORT_FINALIZATION",
    name="deepresearchphase",
)


def upgrade() -> None:
    deep_research_task_status.create(op.get_bind(), checkfirst=True)
    deep_research_phase.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "deep_research_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(length=500), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("max_analysts", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("status", deep_research_task_status, nullable=False),
        sa.Column("phase", deep_research_phase, nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_message", sa.String(length=255), nullable=True),
        sa.Column("current_revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("feedback_round_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_feedback_rounds", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("pending_feedback_text", sa.Text(), nullable=True),
        sa.Column("selected_revision", sa.Integer(), nullable=True),
        sa.Column("final_report_markdown", sa.Text(), nullable=True),
        sa.Column("final_report_summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deep_research_tasks_id"), "deep_research_tasks", ["id"], unique=False)
    op.create_index(op.f("ix_deep_research_tasks_user_id"), "deep_research_tasks", ["user_id"], unique=False)
    op.create_index(op.f("ix_deep_research_tasks_status"), "deep_research_tasks", ["status"], unique=False)
    op.create_index("ix_deep_research_tasks_user_status", "deep_research_tasks", ["user_id", "status"], unique=False)
    op.create_index(
        "ix_deep_research_tasks_user_created_at",
        "deep_research_tasks",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_deep_research_tasks_selected_revision",
        "deep_research_tasks",
        ["selected_revision"],
        unique=False,
    )

    op.create_table(
        "deep_research_analyst_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("analysts_json", sa.JSON(), nullable=True),
        sa.Column("is_selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["deep_research_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "revision_number", name="uq_deep_research_revision_task_revision"),
    )
    op.create_index(
        op.f("ix_deep_research_analyst_revisions_id"),
        "deep_research_analyst_revisions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deep_research_analyst_revisions_task_id"),
        "deep_research_analyst_revisions",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "ix_deep_research_revision_task_selected",
        "deep_research_analyst_revisions",
        ["task_id", "is_selected"],
        unique=False,
    )

    op.create_table(
        "deep_research_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress_message", sa.String(length=255), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["deep_research_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deep_research_runs_id"), "deep_research_runs", ["id"], unique=False)
    op.create_index(op.f("ix_deep_research_runs_task_id"), "deep_research_runs", ["task_id"], unique=False)
    op.create_index(
        "ix_deep_research_runs_task_revision",
        "deep_research_runs",
        ["task_id", "revision_number"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_deep_research_runs_task_revision", table_name="deep_research_runs")
    op.drop_index(op.f("ix_deep_research_runs_task_id"), table_name="deep_research_runs")
    op.drop_index(op.f("ix_deep_research_runs_id"), table_name="deep_research_runs")
    op.drop_table("deep_research_runs")

    op.drop_index("ix_deep_research_revision_task_selected", table_name="deep_research_analyst_revisions")
    op.drop_index(op.f("ix_deep_research_analyst_revisions_task_id"), table_name="deep_research_analyst_revisions")
    op.drop_index(op.f("ix_deep_research_analyst_revisions_id"), table_name="deep_research_analyst_revisions")
    op.drop_table("deep_research_analyst_revisions")

    op.drop_index("ix_deep_research_tasks_selected_revision", table_name="deep_research_tasks")
    op.drop_index("ix_deep_research_tasks_user_created_at", table_name="deep_research_tasks")
    op.drop_index("ix_deep_research_tasks_user_status", table_name="deep_research_tasks")
    op.drop_index(op.f("ix_deep_research_tasks_status"), table_name="deep_research_tasks")
    op.drop_index(op.f("ix_deep_research_tasks_user_id"), table_name="deep_research_tasks")
    op.drop_index(op.f("ix_deep_research_tasks_id"), table_name="deep_research_tasks")
    op.drop_table("deep_research_tasks")

    deep_research_phase.drop(op.get_bind(), checkfirst=True)
    deep_research_task_status.drop(op.get_bind(), checkfirst=True)
