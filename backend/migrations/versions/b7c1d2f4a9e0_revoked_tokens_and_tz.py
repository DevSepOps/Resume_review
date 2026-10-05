"""replace blacklisted_tokens with revoked_tokens; timezone-aware timestamps

Revision ID: b7c1d2f4a9e0
Revises: e3a514dac763
Create Date: 2025-10-20 10:00:00

Old blacklisted tokens (stored raw, no jti) are dropped: they cannot be mapped to
jti values, and every token issued before this release expires within 24h anyway.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7c1d2f4a9e0"
down_revision: Union[str, Sequence[str], None] = "e3a514dac763"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TZ_COLUMNS = {"users": ("created_date", "updated_date"), "resumes": ("created_date", "updated_date")}


def _convert(to_tz: bool) -> None:
    pg = op.get_bind().dialect.name == "postgresql"
    for table, cols in TZ_COLUMNS.items():
        with op.batch_alter_table(table) as batch:
            for col in cols:
                kwargs = {}
                if pg:
                    # existing naive values are UTC (container timezone)
                    # same expression both ways: naive->timestamptz and timestamptz->naive UTC
                    kwargs["postgresql_using"] = f"{col} AT TIME ZONE 'UTC'"
                batch.alter_column(
                    col,
                    type_=sa.DateTime(timezone=to_tz),
                    existing_type=sa.DateTime(timezone=not to_tz),
                    existing_nullable=False,
                    existing_server_default=sa.text("now()"),
                    **kwargs,
                )


def upgrade() -> None:
    op.drop_index(op.f("ix_blacklisted_tokens_user_id"), table_name="blacklisted_tokens")
    op.drop_index(op.f("ix_blacklisted_tokens_token"), table_name="blacklisted_tokens")
    op.drop_table("blacklisted_tokens")

    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_type", sa.String(length=16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_revoked_tokens_jti"), "revoked_tokens", ["jti"], unique=True)
    op.create_index(op.f("ix_revoked_tokens_user_id"), "revoked_tokens", ["user_id"], unique=False)

    _convert(to_tz=True)


def downgrade() -> None:
    _convert(to_tz=False)

    op.drop_index(op.f("ix_revoked_tokens_user_id"), table_name="revoked_tokens")
    op.drop_index(op.f("ix_revoked_tokens_jti"), table_name="revoked_tokens")
    op.drop_table("revoked_tokens")

    op.create_table(
        "blacklisted_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("blacklisted_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_blacklisted_tokens_token"), "blacklisted_tokens", ["token"], unique=True)
    op.create_index(op.f("ix_blacklisted_tokens_user_id"), "blacklisted_tokens", ["user_id"], unique=False)
