"""Protect normalized active exercise names from duplicates.

Revision ID: 20260829_09
Revises: 20260827_08
Create Date: 2026-08-29
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260829_09"
down_revision: str | None = "20260827_08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEX_NAME = "uq_exercises_user_active_name_normalized"


def upgrade() -> None:
    connection = op.get_bind()
    duplicates = connection.execute(
        sa.text(
            """
            SELECT
                user_id,
                lower(btrim(name)) AS normalized_name,
                count(*) AS duplicate_count,
                array_agg(id ORDER BY id) AS exercise_ids,
                array_agg(name ORDER BY id) AS names
            FROM exercises
            WHERE is_archived = false
            GROUP BY user_id, lower(btrim(name))
            HAVING count(*) > 1
            ORDER BY user_id, normalized_name
            """
        )
    ).mappings().all()
    if duplicates:
        details = "; ".join(
            (
                f"user_id={row['user_id']}, normalized_name="
                f"{row['normalized_name']!r}, ids={list(row['exercise_ids'])}, "
                f"names={list(row['names'])}"
            )
            for row in duplicates
        )
        raise RuntimeError(
            "Cannot create active exercise name uniqueness protection; "
            f"resolve existing duplicates first: {details}"
        )

    op.create_index(
        INDEX_NAME,
        "exercises",
        ["user_id", sa.text("lower(btrim(name))")],
        unique=True,
        postgresql_where=sa.text("is_archived = false"),
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="exercises")
