"""learning: init chat sessions and messages

Revision ID: 20260519_learning_init_chat
Revises: 20260510_core_devices
Create Date: 2026-05-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260519_learning_init_chat"
down_revision: str | Sequence[str] | None = "20260510_core_devices"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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
    op.create_index(
        "ix_learning_chat_sessions_user_id",
        "learning_chat_sessions",
        ["user_id"],
    )

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
    op.create_index(
        "ix_learning_chat_messages_session_id",
        "learning_chat_messages",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_learning_chat_messages_session_id",
        table_name="learning_chat_messages",
    )
    op.drop_table("learning_chat_messages")
    op.drop_index(
        "ix_learning_chat_sessions_user_id",
        table_name="learning_chat_sessions",
    )
    op.drop_table("learning_chat_sessions")
