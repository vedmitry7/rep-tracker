"""Add raw user activity events for admin analytics.

Revision ID: 20260907_13
Revises: 20260906_12
Create Date: 2026-09-07
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260907_13"
down_revision: str | None = "20260906_12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Keep existing users' activity unknown instead of inventing a last activity time.
    op.add_column("users", sa.Column("last_active_at", sa.DateTime(timezone=True)))
    op.add_column(
        "users",
        sa.Column("is_blocked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.alter_column("users", "is_blocked", server_default=None)

    op.create_table(
        "user_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_type IN ('start', 'exercise_created', 'result_added', "
            "'stats_opened', 'weekly_report_opened', 'import_used', 'export_used', "
            "'weekly_delivery_failed')",
            name=op.f("ck_user_events_event_type_known"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name=op.f("fk_user_events_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_events")),
    )
    op.create_index("ix_user_events_created_at", "user_events", ["created_at"])
    op.create_index(
        "ix_user_events_user_id_created_at", "user_events", ["user_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_user_events_user_id_created_at", table_name="user_events")
    op.drop_index("ix_user_events_created_at", table_name="user_events")
    op.drop_table("user_events")
    op.drop_column("users", "is_blocked")
    op.drop_column("users", "last_active_at")
