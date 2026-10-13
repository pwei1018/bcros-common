"""Add BC Notify callback event table.

Revision ID: b7c4d2e9f610
Revises: 9c2e7a1f4d5b
Create Date: 2026-10-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b7c4d2e9f610"
down_revision = "9c2e7a1f4d5b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bc_notify_callback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event", sa.String(), nullable=False),
        sa.Column("notification_id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("notify_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("status_display_name", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bc_notify_callback_notification_id", "bc_notify_callback", ["notification_id"])
    op.create_index("ix_bc_notify_callback_notify_id", "bc_notify_callback", ["notify_id"])


def downgrade():
    op.drop_index("ix_bc_notify_callback_notify_id", table_name="bc_notify_callback")
    op.drop_index("ix_bc_notify_callback_notification_id", table_name="bc_notify_callback")
    op.drop_table("bc_notify_callback")