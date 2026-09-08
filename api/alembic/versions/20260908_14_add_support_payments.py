"""Add durable Telegram Stars support payments.

Revision ID: 20260908_14
Revises: 20260907_13
Create Date: 2026-09-08
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260908_14"
down_revision: str | None = "20260907_13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "support_payments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("invoice_payload", sa.String(length=64), nullable=False),
        sa.Column("telegram_payment_charge_id", sa.String(length=255)),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("refunded_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name=op.f("ck_support_payments_amount_positive")),
        sa.CheckConstraint(
            "status IN ('pending', 'succeeded', 'expired', 'refunded')",
            name=op.f("ck_support_payments_status_known"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_support_payments")),
        sa.UniqueConstraint("invoice_payload", name=op.f("uq_support_payments_invoice_payload")),
        sa.UniqueConstraint(
            "telegram_payment_charge_id",
            name=op.f("uq_support_payments_telegram_payment_charge_id"),
        ),
    )
    op.create_index(
        op.f("ix_support_payments_telegram_user_id"),
        "support_payments",
        ["telegram_user_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_support_payments_telegram_user_id"), table_name="support_payments")
    op.drop_table("support_payments")
