"""Add performed_on to exercise entries.

Revision ID: 20260827_05
Revises: 20260827_04
Create Date: 2026-08-27
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260827_05"
down_revision: str | None = "20260827_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "exercise_entries",
        sa.Column(
            "performed_on",
            sa.Date(),
            server_default=sa.text("CURRENT_DATE"),
            nullable=False,
        ),
    )
    op.alter_column(
        "exercise_entries",
        "performed_on",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("exercise_entries", "performed_on")
