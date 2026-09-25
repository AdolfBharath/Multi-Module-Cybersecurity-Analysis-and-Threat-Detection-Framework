"""production security hardening

Revision ID: 20260925_0001
Revises:
Create Date: 2026-09-25
"""

from alembic import op
import sqlalchemy as sa

from app.db.models import *  # noqa: F401,F403
from app.db.session import Base


revision = "20260925_0001"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(bind, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _has_column(bind, table_name: str, column_name: str) -> bool:
    if not _has_table(bind, table_name):
        return False
    return column_name in {column["name"] for column in sa.inspect(bind).get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_table(bind, "users"):
        Base.metadata.create_all(bind=bind)
        return
    if not _has_table(bind, "organizations"):
        op.create_table(
            "organizations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("slug", sa.String(length=120), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_organizations_name", "organizations", ["name"], unique=True)
        op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    if not _has_table(bind, "teams"):
        op.create_table(
            "teams",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_teams_organization_id", "teams", ["organization_id"])
        op.create_index("ix_teams_name", "teams", ["name"])
    for column in [
        sa.Column("mfa_secret_encrypted", sa.Text(), nullable=False, server_default=""),
        sa.Column("force_password_change", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
    ]:
        if not _has_column(bind, "users", column.name):
            op.add_column("users", column)
    if _has_table(bind, "users") and not _has_column(bind, "users", "organization_id_tmp_fk_marker"):
        try:
            op.create_foreign_key("fk_users_organization_id_organizations", "users", "organizations", ["organization_id"], ["id"])
        except Exception:
            pass
        try:
            op.create_index("ix_users_organization_id", "users", ["organization_id"])
        except Exception:
            pass
    if not _has_column(bind, "sessions", "refresh_jti"):
        op.add_column("sessions", sa.Column("refresh_jti", sa.String(length=80), nullable=False, server_default=""))
        op.create_index("ix_sessions_refresh_jti", "sessions", ["refresh_jti"])
    if not _has_table(bind, "password_reset_tokens"):
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
        op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)
    if not _has_table(bind, "email_verification_tokens"):
        op.create_table(
            "email_verification_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_email_verification_tokens_user_id", "email_verification_tokens", ["user_id"])
        op.create_index("ix_email_verification_tokens_token_hash", "email_verification_tokens", ["token_hash"], unique=True)
    if not _has_table(bind, "mfa_recovery_codes"):
        op.create_table(
            "mfa_recovery_codes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("code_hash", sa.String(length=128), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_mfa_recovery_codes_user_id", "mfa_recovery_codes", ["user_id"])
        op.create_index("ix_mfa_recovery_codes_code_hash", "mfa_recovery_codes", ["code_hash"])


def downgrade() -> None:
    bind = op.get_bind()
    for table in ["mfa_recovery_codes", "email_verification_tokens", "password_reset_tokens", "teams", "organizations"]:
        if _has_table(bind, table):
            op.drop_table(table)
    if _has_column(bind, "sessions", "refresh_jti"):
        op.drop_column("sessions", "refresh_jti")
    for column_name in ["organization_id", "locked_until", "failed_login_count", "force_password_change", "mfa_secret_encrypted"]:
        if _has_column(bind, "users", column_name):
            op.drop_column("users", column_name)
