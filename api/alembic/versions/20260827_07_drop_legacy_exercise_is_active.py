"""Drop the unused legacy exercise is_active flag.

Revision ID: 20260827_07
Revises: 20260827_06
Create Date: 2026-08-27
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260827_07"
down_revision: str | None = "20260827_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("exercises", "is_active")


def downgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )
