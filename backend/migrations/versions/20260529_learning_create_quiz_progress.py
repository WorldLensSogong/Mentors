"""learning: create quiz progress table

Revision ID: 20260529_learning_quiz_progress
Revises: 20260515_growth
Create Date: 2026-05-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260529_learning_quiz_progress"
down_revision: str | Sequence[str] | None = "20260515_growth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learning_quiz_progress",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_id", sa.String(length=64), nullable=False),
        sa.Column("concept_id", sa.BigInteger(), nullable=False),
        sa.Column("tier", sa.String(length=10), nullable=False),
        sa.Column("last_answer_index", sa.Integer(), nullable=False),
        sa.Column("last_result_correct", sa.Boolean(), nullable=False),
        sa.Column("solved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id",
            "question_id",
            name="uq_learning_quiz_progress_user_question",
        ),
    )
    op.create_index(
        "ix_learning_quiz_progress_user_id",
        "learning_quiz_progress",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_learning_quiz_progress_user_id",
        table_name="learning_quiz_progress",
    )
    op.drop_table("learning_quiz_progress")
