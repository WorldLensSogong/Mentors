"""learning: backfill missing chat and quiz tables

Revision ID: 20260526_learning_backfill
Revises: 20260523_auth_local_credentials
Create Date: 2026-05-26

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260526_learning_backfill"
down_revision: str | Sequence[str] | None = "20260523_auth_local_credentials"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _has_table("learning_chat_sessions"):
        op.create_table(
            "learning_chat_sessions",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column(
                "user_id",
                sa.BigInteger(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("mentor_id", sa.BigInteger(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=True),
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

    if _has_table("learning_chat_sessions") and not _has_index(
        "learning_chat_sessions", "ix_learning_chat_sessions_user_id"
    ):
        op.create_index(
            "ix_learning_chat_sessions_user_id",
            "learning_chat_sessions",
            ["user_id"],
        )

    if not _has_table("learning_chat_messages"):
        op.create_table(
            "learning_chat_messages",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column(
                "session_id",
                sa.BigInteger(),
                sa.ForeignKey("learning_chat_sessions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    if _has_table("learning_chat_messages") and not _has_index(
        "learning_chat_messages", "ix_learning_chat_messages_session_id"
    ):
        op.create_index(
            "ix_learning_chat_messages_session_id",
            "learning_chat_messages",
            ["session_id"],
        )

    if not _has_table("learning_quiz_attempts"):
        op.create_table(
            "learning_quiz_attempts",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column(
                "user_id",
                sa.BigInteger(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("concept_id", sa.BigInteger(), nullable=False),
            sa.Column("quiz_index", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("correct", sa.Boolean(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if _has_table("learning_quiz_attempts") and not _has_index(
        "learning_quiz_attempts", "ix_learning_quiz_attempts_user_concept"
    ):
        op.create_index(
            "ix_learning_quiz_attempts_user_concept",
            "learning_quiz_attempts",
            ["user_id", "concept_id"],
            unique=False,
        )


def downgrade() -> None:
    if _has_table("learning_quiz_attempts") and _has_index(
        "learning_quiz_attempts", "ix_learning_quiz_attempts_user_concept"
    ):
        op.drop_index(
            "ix_learning_quiz_attempts_user_concept",
            table_name="learning_quiz_attempts",
        )
    if _has_table("learning_quiz_attempts"):
        op.drop_table("learning_quiz_attempts")

    if _has_table("learning_chat_messages") and _has_index(
        "learning_chat_messages", "ix_learning_chat_messages_session_id"
    ):
        op.drop_index(
            "ix_learning_chat_messages_session_id",
            table_name="learning_chat_messages",
        )
    if _has_table("learning_chat_messages"):
        op.drop_table("learning_chat_messages")

    if _has_table("learning_chat_sessions") and _has_index(
        "learning_chat_sessions", "ix_learning_chat_sessions_user_id"
    ):
        op.drop_index(
            "ix_learning_chat_sessions_user_id",
            table_name="learning_chat_sessions",
        )
    if _has_table("learning_chat_sessions"):
        op.drop_table("learning_chat_sessions")
