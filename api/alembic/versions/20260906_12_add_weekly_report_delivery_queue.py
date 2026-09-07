"""Add durable delivery queue state to weekly reports.

Revision ID: 20260906_12
Revises: 20260906_11
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260906_12"
down_revision: str | None = "20260906_11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "weekly_reports",
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "weekly_reports",
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column("weekly_reports", sa.Column("locked_until", sa.DateTime(timezone=True)))
    op.add_column("weekly_reports", sa.Column("lock_token", postgresql.UUID(as_uuid=True)))
    op.add_column("weekly_reports", sa.Column("locked_by", sa.String(length=64)))
    op.add_column("weekly_reports", sa.Column("last_error", sa.Text()))
    op.add_column("weekly_reports", sa.Column("sent_at", sa.DateTime(timezone=True)))
    op.add_column(
        "weekly_reports",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # These are only old delivery-state values. Existing report snapshots and
    # user workout data remain untouched.
    op.execute("""
        UPDATE weekly_reports
        SET status = 'retry'
        WHERE status IN ('claimed', 'failed')
    """)
    op.alter_column("weekly_reports", "status", server_default="pending")
    op.create_check_constraint(
        "weekly_reports_delivery_status",
        "weekly_reports",
        "status IN ('pending', 'processing', 'sent', 'retry', 'failed')",
    )
    op.create_check_constraint(
        "weekly_reports_attempts_nonnegative",
        "weekly_reports",
        "attempts >= 0",
    )
    op.create_index(
        "ix_weekly_reports_available_delivery",
        "weekly_reports",
        ["next_attempt_at", "created_at"],
        postgresql_where=sa.text("status IN ('pending', 'retry')"),
    )
    op.create_index(
        "ix_weekly_reports_expired_lease",
        "weekly_reports",
        ["locked_until"],
        postgresql_where=sa.text("status = 'processing'"),
    )


def downgrade() -> None:
    op.drop_index("ix_weekly_reports_expired_lease", table_name="weekly_reports")
    op.drop_index("ix_weekly_reports_available_delivery", table_name="weekly_reports")
    op.drop_constraint("weekly_reports_attempts_nonnegative", "weekly_reports", type_="check")
    op.drop_constraint("weekly_reports_delivery_status", "weekly_reports", type_="check")
    op.alter_column("weekly_reports", "status", server_default=None)
    op.drop_column("weekly_reports", "updated_at")
    op.drop_column("weekly_reports", "sent_at")
    op.drop_column("weekly_reports", "last_error")
    op.drop_column("weekly_reports", "locked_by")
    op.drop_column("weekly_reports", "lock_token")
    op.drop_column("weekly_reports", "locked_until")
    op.drop_column("weekly_reports", "next_attempt_at")
    op.drop_column("weekly_reports", "attempts")
