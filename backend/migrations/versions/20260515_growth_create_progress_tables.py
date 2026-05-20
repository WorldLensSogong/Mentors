"""growth: create progress tables

Revision ID: 20260515_growth
Revises: 20260513_onboarding
Create Date: 2026-05-15

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260515_growth"
down_revision: str | Sequence[str] | None = "20260513_onboarding"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tier_states",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("current_tier", sa.String(length=10), nullable=False, server_default="T1"),
        sa.Column("mastered_concepts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_concepts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("promotion_eligible_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_promotion_attempt_at", sa.DateTime(timezone=True), nullable=True),
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
    )

    op.create_table(
        "concept_masteries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tier", sa.String(length=10), nullable=False),
        sa.Column("concept_id", sa.BigInteger(), nullable=False),
        sa.Column("source_event_id", sa.String(length=64), nullable=False),
        sa.Column(
            "mastered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "concept_id", name="uq_concept_masteries_user_concept"),
        sa.UniqueConstraint("source_event_id", name="uq_concept_masteries_source_event"),
    )
    op.create_index("ix_concept_masteries_user_id", "concept_masteries", ["user_id"])

    op.create_table(
        "promotion_test_attempts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("current_tier", sa.String(length=10), nullable=False),
        sa.Column("target_tier", sa.String(length=10), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("correct_answers", sa.Integer(), nullable=False),
        sa.Column("score_percent", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("answers_json", sa.Text(), nullable=False),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_promotion_test_attempts_user_id",
        "promotion_test_attempts",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_promotion_test_attempts_user_id", table_name="promotion_test_attempts")
    op.drop_table("promotion_test_attempts")
    op.drop_index("ix_concept_masteries_user_id", table_name="concept_masteries")
    op.drop_table("concept_masteries")
    op.drop_table("tier_states")
