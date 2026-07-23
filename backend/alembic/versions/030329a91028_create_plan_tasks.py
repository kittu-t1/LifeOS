"""create plan_tasks (execution engine) + backfill from existing weekly_plan JSON

Revision ID: 030329a91028
Revises: 78d22a4bd957
Create Date: 2026-07-22 00:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '030329a91028'
down_revision: Union[str, Sequence[str], None] = '78d22a4bd957'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'plan_tasks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('plan_id', sa.Uuid(), nullable=False),
        sa.Column('milestone_id', sa.Uuid(), nullable=True),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('PENDING', 'COMPLETED', name='plan_task_status', native_enum=False),
            nullable=False,
        ),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_plan_tasks_plan_id'), 'plan_tasks', ['plan_id'], unique=False)

    # Backfill: every Plan that existed before the Execution Engine phase
    # has its actions trapped in weekly_plan JSON only - turn each task
    # (old shape: a plain string; see app/planner/prompts.py planner_v2
    # for the new {title, description, estimated_minutes} shape new plans
    # generate) into a real PlanTask row so existing plans aren't left
    # behind by this phase.
    bind = op.get_bind()
    plans = bind.execute(sa.text("SELECT id, weekly_plan FROM plans")).fetchall()

    insert_stmt = sa.text(
        """
        INSERT INTO plan_tasks
            (id, plan_id, milestone_id, week_number, day_number, title, description,
             estimated_minutes, display_order, status, completed_at, created_at, updated_at)
        VALUES
            (:id, :plan_id, NULL, :week_number, NULL, :title, :description,
             :estimated_minutes, :display_order, 'PENDING', NULL, now(), now())
        """
    )

    for plan_id, weekly_plan in plans:
        display_order = 0
        for week in weekly_plan or []:
            week_number = week.get("week")
            for task in week.get("tasks") or []:
                if isinstance(task, str):
                    title, description, estimated_minutes = task, None, None
                else:
                    title = task.get("title", "")
                    description = task.get("description") or None
                    estimated_minutes = task.get("estimated_minutes")
                if not title:
                    continue
                bind.execute(
                    insert_stmt,
                    {
                        "id": str(uuid.uuid4()),
                        "plan_id": plan_id,
                        "week_number": week_number,
                        "title": title,
                        "description": description,
                        "estimated_minutes": estimated_minutes,
                        "display_order": display_order,
                    },
                )
                display_order += 1


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_plan_tasks_plan_id'), table_name='plan_tasks')
    op.drop_table('plan_tasks')
