"""Allow users to include individual exercises in weekly reports.

Revision ID: 20260906_11
Revises: 20260906_10
Create Date: 2026-09-06
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260906_11"
down_revision: str | None = "20260906_10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column(
            "weekly_report_enabled",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("exercises", "weekly_report_enabled")
