"""Add language to users.

Revision ID: 20260827_08
Revises: 20260827_07
Create Date: 2026-08-27
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260827_08"
down_revision: str | None = "20260827_07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "language",
            sa.String(length=2),
            server_default="ru",
            nullable=False,
        ),
    )
    op.alter_column("users", "language", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "language")
