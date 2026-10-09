"""Add provider response ID to active notifications.

Revision ID: d4e9f2a6c801
Revises: c3d8a1f6b902
Create Date: 2026-10-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d4e9f2a6c801"
down_revision = "c3d8a1f6b902"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("notification", sa.Column("notify_response_id", sa.String(), nullable=True))
    op.create_index("ix_notification_notify_response_id", "notification", ["notify_response_id"])


def downgrade():
    op.drop_index("ix_notification_notify_response_id", table_name="notification")
    op.drop_column("notification", "notify_response_id")