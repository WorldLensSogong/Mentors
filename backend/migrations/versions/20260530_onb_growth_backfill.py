"""onboarding/growth: backfill missing tables from out-of-sync alembic stamp

Revision ID: 20260530_onb_growth_backfill
Revises: 20260528_content_seed_pool, 20260529_learning_quiz_progress
Create Date: 2026-05-30

NOTE: revision id is kept <=32 chars to fit the default
`alembic_version.version_num VARCHAR(32)` column.

Some local dev environments end up with `alembic_version` stamped past
`20260513_onboarding` and `20260515_growth` without their DDL actually
applied. Result: `user_profiles`, `onboarding_survey_answers`,
`tier_states`, `concept_masteries`, `promotion_test_attempts` are missing
while alembic still considers those migrations applied (so
`alembic upgrade head` is a no-op for them and the app crashes at runtime
with `relation "user_profiles" does not exist`).

This migration:
  1. **Merges the two existing heads** (`20260528_content_seed_pool` and
     `20260529_learning_quiz_progress`) so future upgrades produce a
     single head instead of branching.
  2. **Backfills any of the 5 missing tables/indexes idempotently** using
     the same `_has_table`/`_has_index` guard pattern already established
     in `20260526_learning_backfill`.

Safe to run repeatedly: every `create_table`/`create_index` is guarded.
Environments where the tables already exist (correctly applied) are
unaffected — the upgrade becomes a no-op for them.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260530_onb_growth_backfill"
down_revision: tuple[str, ...] = (
    "20260528_content_seed_pool",
    "20260529_learning_quiz_progress",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    # 1. onboarding (originally 20260513_onboarding)
    if not _has_table("user_profiles"):
        op.create_table(
            "user_profiles",
            sa.Column(
                "user_id",
                sa.BigInteger(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("current_tier", sa.String(length=10), nullable=False, server_default="T1"),
            sa.Column("selected_mentor_id", sa.BigInteger(), nullable=True),
            sa.Column("selected_mentor_slug", sa.String(length=100), nullable=True),
            sa.Column("risk_profile", sa.String(length=50), nullable=True),
            sa.Column("experience_level", sa.String(length=50), nullable=True),
            sa.Column("learning_goal", sa.String(length=100), nullable=True),
            sa.Column("preferred_style", sa.String(length=50), nullable=True),
            sa.Column("interests_json", sa.Text(), nullable=True),
            sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
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

    if not _has_table("onboarding_survey_answers"):
        op.create_table(
            "onboarding_survey_answers",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column(
                "user_id",
                sa.BigInteger(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("question_code", sa.String(length=100), nullable=False),
            sa.Column("question_text", sa.String(length=255), nullable=True),
            sa.Column("answer_value", sa.Text(), nullable=True),
            sa.Column("answer_payload_json", sa.Text(), nullable=True),
            sa.Column(
                "answered_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    if _has_table("onboarding_survey_answers") and not _has_index(
        "onboarding_survey_answers", "ix_onboarding_survey_answers_user_id"
    ):
        op.create_index(
            "ix_onboarding_survey_answers_user_id",
            "onboarding_survey_answers",
            ["user_id"],
        )

    # 2. growth (originally 20260515_growth)
    if not _has_table("tier_states"):
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

    if not _has_table("concept_masteries"):
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

    if _has_table("concept_masteries") and not _has_index(
        "concept_masteries", "ix_concept_masteries_user_id"
    ):
        op.create_index("ix_concept_masteries_user_id", "concept_masteries", ["user_id"])

    if not _has_table("promotion_test_attempts"):
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

    if _has_table("promotion_test_attempts") and not _has_index(
        "promotion_test_attempts", "ix_promotion_test_attempts_user_id"
    ):
        op.create_index(
            "ix_promotion_test_attempts_user_id",
            "promotion_test_attempts",
            ["user_id"],
        )


def downgrade() -> None:
    # Reverse order — guards keep this idempotent on partial states.
    if _has_table("promotion_test_attempts") and _has_index(
        "promotion_test_attempts", "ix_promotion_test_attempts_user_id"
    ):
        op.drop_index(
            "ix_promotion_test_attempts_user_id",
            table_name="promotion_test_attempts",
        )
    if _has_table("promotion_test_attempts"):
        op.drop_table("promotion_test_attempts")

    if _has_table("concept_masteries") and _has_index(
        "concept_masteries", "ix_concept_masteries_user_id"
    ):
        op.drop_index("ix_concept_masteries_user_id", table_name="concept_masteries")
    if _has_table("concept_masteries"):
        op.drop_table("concept_masteries")

    if _has_table("tier_states"):
        op.drop_table("tier_states")

    if _has_table("onboarding_survey_answers") and _has_index(
        "onboarding_survey_answers", "ix_onboarding_survey_answers_user_id"
    ):
        op.drop_index(
            "ix_onboarding_survey_answers_user_id",
            table_name="onboarding_survey_answers",
        )
    if _has_table("onboarding_survey_answers"):
        op.drop_table("onboarding_survey_answers")

    if _has_table("user_profiles"):
        op.drop_table("user_profiles")
