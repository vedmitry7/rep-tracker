"""Persist weekly report snapshots and delivery claims."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260906_10"
down_revision = "20260829_09"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("weekly_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "week_start"))


def downgrade():
    op.drop_table("weekly_reports")
