"""Rename provider-specific notification history columns.

Revision ID: c3d8a1f6b902
Revises: b7c4d2e9f610
Create Date: 2026-10-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c3d8a1f6b902"
down_revision = "b7c4d2e9f610"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "notification_history",
        "gc_notify_response_id",
        new_column_name="notify_response_id",
        existing_type=sa.String(),
        existing_nullable=True,
    )
    op.alter_column(
        "notification_history",
        "gc_notify_status",
        new_column_name="notify_status",
        existing_type=sa.String(),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "notification_history",
        "notify_status",
        new_column_name="gc_notify_status",
        existing_type=sa.String(),
        existing_nullable=True,
    )
    op.alter_column(
        "notification_history",
        "notify_response_id",
        new_column_name="gc_notify_response_id",
        existing_type=sa.String(),
        existing_nullable=True,
    )
