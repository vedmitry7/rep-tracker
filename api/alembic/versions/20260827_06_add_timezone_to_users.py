"""Add timezone to users.

Revision ID: 20260827_06
Revises: 20260827_05
Create Date: 2026-08-27
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260827_06"
down_revision: str | None = "20260827_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "timezone",
            sa.String(length=255),
            server_default="Europe/Moscow",
            nullable=False,
        ),
    )
    op.alter_column("users", "timezone", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "timezone")
