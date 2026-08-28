"""Add is_banned to users.

Revision ID: 20260827_02
Revises: 20260827_01
Create Date: 2026-08-27
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260827_02"
down_revision: str | None = "20260827_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_banned",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_banned")
