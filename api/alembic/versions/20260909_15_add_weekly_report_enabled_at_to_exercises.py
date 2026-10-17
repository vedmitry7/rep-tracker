"""Track when weekly reporting started for an exercise.

Revision ID: 20260909_15
Revises: 20260908_14
Create Date: 2026-09-09
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260909_15"
down_revision: str | None = "20260908_14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column(
            "weekly_report_enabled_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
    )
    # Existing exercises keep the two-full-week grace period measured from their
    # original creation so already-running reports are not disabled retroactively
    # before a comparable tracking window has elapsed.
    op.execute(
        "UPDATE exercises SET weekly_report_enabled_at = created_at "
        "WHERE weekly_report_enabled_at IS NULL"
    )


def downgrade() -> None:
    op.drop_column("exercises", "weekly_report_enabled_at")
