"""Replace set entries with exercise entries.

Revision ID: 20260827_04
Revises: 20260827_03
Create Date: 2026-08-27
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260827_04"
down_revision: str | None = "20260827_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("set_entries")
    op.create_table(
        "exercise_entries",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("exercise_id", sa.BigInteger(), nullable=False),
        sa.Column("reps", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "cardinality(reps) > 0",
            name=op.f("ck_exercise_entries_reps_not_empty"),
        ),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
            name="fk_exercise_entries_exercise_id_exercises",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_exercise_entries"),
    )
    op.create_index(
        "ix_exercise_entries_exercise_id",
        "exercise_entries",
        ["exercise_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_exercise_entries_exercise_id",
        table_name="exercise_entries",
    )
    op.drop_table("exercise_entries")
    op.create_table(
        "set_entries",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("exercise_id", sa.BigInteger(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "reps > 0",
            name=op.f("ck_set_entries_reps_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
            name="fk_set_entries_exercise_id_exercises",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_set_entries"),
    )
    op.create_index(
        "ix_set_entries_exercise_id_performed_at",
        "set_entries",
        ["exercise_id", "performed_at"],
        unique=False,
    )
    op.create_index(
        "ix_set_entries_performed_at",
        "set_entries",
        ["performed_at"],
        unique=False,
    )
