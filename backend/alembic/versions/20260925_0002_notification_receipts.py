"""Track broadcast notification state independently for each recipient."""
from alembic import op
import sqlalchemy as sa

revision = "20260925_0002"
down_revision = "20260925_0001"
branch_labels = None
depends_on = None


def upgrade():
    if not sa.inspect(op.get_bind()).has_table("notification_receipts"):
        op.create_table(
            "notification_receipts",
            sa.Column("notification_id", sa.Integer(), sa.ForeignKey("notifications.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("status", sa.String(40), nullable=False),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade():
    op.drop_table("notification_receipts")
