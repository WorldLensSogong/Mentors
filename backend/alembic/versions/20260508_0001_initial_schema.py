"""initial schema

Revision ID: 20260508_0001
Revises:
Create Date: 2026-05-08 10:30:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260508_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "level_definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("level_no", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("min_xp", sa.Integer(), nullable=False),
        sa.Column("unlock_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("level_no"),
    )

    op.create_table(
        "investment_strategies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("principle_summary", sa.Text(), nullable=True),
        sa.Column("risk_profile_tag", sa.String(length=30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "interest_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "news_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("nickname", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("nickname"),
    )

    op.create_table(
        "mentors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("unlock_level_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("one_liner", sa.String(length=255), nullable=True),
        sa.Column("philosophy", sa.Text(), nullable=True),
        sa.Column("speaking_style", sa.Text(), nullable=True),
        sa.Column("prompt_template", sa.Text(), nullable=True),
        sa.Column("is_free", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["investment_strategies.id"]),
        sa.ForeignKeyConstraint(["unlock_level_id"], ["level_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "auth_identities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),
    )

    op.create_table(
        "mentor_focus_topics",
        sa.Column("mentor_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["mentor_id"], ["mentors.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["interest_topics.id"]),
        sa.PrimaryKeyConstraint("mentor_id", "topic_id"),
    )

    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("original_url", sa.String(length=1000), nullable=False),
        sa.Column("publisher", sa.String(length=100), nullable=True),
        sa.Column("author_name", sa.String(length=100), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=1000), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("original_url"),
    )

    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("current_level_id", sa.Integer(), nullable=False),
        sa.Column("current_mentor_id", sa.Integer(), nullable=True),
        sa.Column("age_band", sa.String(length=30), nullable=True),
        sa.Column("has_investment_experience", sa.Boolean(), nullable=False),
        sa.Column("investment_experience_months", sa.Integer(), nullable=True),
        sa.Column("holdings_summary", sa.Text(), nullable=True),
        sa.Column("investment_amount_band", sa.String(length=50), nullable=True),
        sa.Column("investment_purpose", sa.String(length=100), nullable=True),
        sa.Column("risk_tolerance", sa.String(length=30), nullable=True),
        sa.Column("learning_stage", sa.String(length=30), nullable=False),
        sa.Column("total_xp", sa.Integer(), nullable=False),
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["current_level_id"], ["level_definitions.id"]),
        sa.ForeignKeyConstraint(["current_mentor_id"], ["mentors.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "onboarding_survey_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_code", sa.String(length=50), nullable=False),
        sa.Column("question_text", sa.String(length=255), nullable=True),
        sa.Column("answer_value", sa.Text(), nullable=True),
        sa.Column("answer_payload", sa.Text(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_interest_topics",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["topic_id"], ["interest_topics.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "topic_id"),
    )

    op.create_table(
        "article_topics",
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["news_articles.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["interest_topics.id"]),
        sa.PrimaryKeyConstraint("article_id", "topic_id"),
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("mentor_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("session_status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["mentor_id"], ["mentors.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "daily_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("mentor_id", sa.Integer(), nullable=False),
        sa.Column("level_id", sa.Integer(), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("outlook_text", sa.Text(), nullable=True),
        sa.Column("learning_question_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["level_id"], ["level_definitions.id"]),
        sa.ForeignKeyConstraint(["mentor_id"], ["mentors.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "mentor_id", "report_date", name="uq_daily_report"),
    )

    op.create_table(
        "learning_modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("level_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("concept_summary", sa.Text(), nullable=True),
        sa.Column("quiz_question", sa.Text(), nullable=True),
        sa.Column("quiz_answer_text", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["level_id"], ["level_definitions.id"]),
        sa.ForeignKeyConstraint(["strategy_id"], ["investment_strategies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("mentor_id", sa.Integer(), nullable=True),
        sa.Column("sender_type", sa.String(length=20), nullable=False),
        sa.Column("message_type", sa.String(length=20), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["mentor_id"], ["mentors.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("learning_modules")
    op.drop_table("daily_reports")
    op.drop_table("chat_sessions")
    op.drop_table("article_topics")
    op.drop_table("user_interest_topics")
    op.drop_table("onboarding_survey_answers")
    op.drop_table("user_profiles")
    op.drop_table("news_articles")
    op.drop_table("mentor_focus_topics")
    op.drop_table("auth_identities")
    op.drop_table("mentors")
    op.drop_table("users")
    op.drop_table("news_sources")
    op.drop_table("interest_topics")
    op.drop_table("investment_strategies")
    op.drop_table("level_definitions")
