"""create plans milestones planner_runs

Revision ID: 06c5868d6a17
Revises: da1eec629c65
Create Date: 2026-07-20 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "06c5868d6a17"
down_revision: Union[str, Sequence[str], None] = "da1eec629c65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("mission", sa.Text(), nullable=False),
        sa.Column("estimated_duration", sa.String(length=100), nullable=False),
        sa.Column("timeline", sa.JSON(), nullable=False),
        sa.Column("weekly_plan", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plans_goal_id"), "plans", ["goal_id"], unique=False)

    op.create_table(
        "milestones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration", sa.String(length=100), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_milestones_plan_id"), "milestones", ["plan_id"], unique=False)

    op.create_table(
        "planner_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=True),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("model_used", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("SUCCESS", "FAILED", name="planner_run_status", native_enum=False),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_planner_runs_goal_id"), "planner_runs", ["goal_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_planner_runs_goal_id"), table_name="planner_runs")
    op.drop_table("planner_runs")
    op.drop_index(op.f("ix_milestones_plan_id"), table_name="milestones")
    op.drop_table("milestones")
    op.drop_index(op.f("ix_plans_goal_id"), table_name="plans")
    op.drop_table("plans")
