"""Create initial tables.

Revision ID: 20260827_01
Revises:
Create Date: 2026-08-27
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260827_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )

    op.create_table(
        "user_identities",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "btrim(external_id) <> ''",
            name=op.f("ck_user_identities_external_id_not_blank"),
        ),
        sa.CheckConstraint(
            "btrim(provider) <> ''",
            name=op.f("ck_user_identities_provider_not_blank"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_identities_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_identities"),
        sa.UniqueConstraint(
            "provider",
            "external_id",
            name="uq_user_identities_provider_external_id",
        ),
    )
    op.create_index(
        "ix_user_identities_user_id",
        "user_identities",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "exercises",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "btrim(name) <> ''",
            name=op.f("ck_exercises_name_not_blank"),
        ),
        sa.CheckConstraint(
            "position >= 0",
            name=op.f("ck_exercises_position_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_exercises_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_exercises"),
    )
    op.create_index("ix_exercises_user_id", "exercises", ["user_id"], unique=False)

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


def downgrade() -> None:
    op.drop_index("ix_set_entries_performed_at", table_name="set_entries")
    op.drop_index(
        "ix_set_entries_exercise_id_performed_at",
        table_name="set_entries",
    )
    op.drop_table("set_entries")
    op.drop_index("ix_exercises_user_id", table_name="exercises")
    op.drop_table("exercises")
    op.drop_index("ix_user_identities_user_id", table_name="user_identities")
    op.drop_table("user_identities")
    op.drop_table("users")
