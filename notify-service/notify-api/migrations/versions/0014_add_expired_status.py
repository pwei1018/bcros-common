"""add EXPIRED status

Revision ID: 9c2e7a1f4d5b
Revises: 8a1c4f2d9b3e
Create Date: 2026-09-22 15:35:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "9c2e7a1f4d5b"
down_revision = "8a1c4f2d9b3e"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "INSERT INTO notification_status VALUES("
        "'EXPIRED', "
        "'Notification could not be delivered within the retention window and was archived', "
        "false)"
    )


def downgrade():
    op.execute("DELETE FROM notification_status WHERE code='EXPIRED'")
