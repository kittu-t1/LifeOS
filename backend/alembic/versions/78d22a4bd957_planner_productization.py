"""planner productization - deadline, plan updated_at, milestone created_at, one plan per goal

Revision ID: 78d22a4bd957
Revises: 06c5868d6a17
Create Date: 2026-07-20 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "78d22a4bd957"
down_revision: Union[str, Sequence[str], None] = "06c5868d6a17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("goals", sa.Column("deadline", sa.DateTime(timezone=True), nullable=True))

    op.add_column(
        "plans",
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.add_column(
        "milestones",
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    # Plan becomes one-per-Goal as of this phase (see app/models/plan.py).
    # If this environment already generated + regenerated plans under the
    # old "one row per generation" design, there may be more than one
    # Plan per goal_id - clean that up defensively before adding the
    # unique constraint, keeping only the most recent Plan per goal
    # (matches what GET /planner/goals/{goal_id} was already serving as
    # "the" plan under the old ORDER BY created_at DESC LIMIT 1 design).
    op.execute("""
        UPDATE planner_runs
        SET plan_id = NULL
        WHERE plan_id IN (
            SELECT id FROM plans
            WHERE id NOT IN (
                SELECT DISTINCT ON (goal_id) id FROM plans ORDER BY goal_id, created_at DESC
            )
        )
        """)
    op.execute("""
        DELETE FROM plans
        WHERE id NOT IN (
            SELECT DISTINCT ON (goal_id) id FROM plans ORDER BY goal_id, created_at DESC
        )
        """)

    op.drop_index(op.f("ix_plans_goal_id"), table_name="plans")
    op.create_index(op.f("ix_plans_goal_id"), "plans", ["goal_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_plans_goal_id"), table_name="plans")
    op.create_index(op.f("ix_plans_goal_id"), "plans", ["goal_id"], unique=False)
    op.drop_column("milestones", "created_at")
    op.drop_column("plans", "updated_at")
    op.drop_column("goals", "deadline")
