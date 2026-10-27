"""add bc_notify_sms provider

Revision ID: e5a1b7c3d902
Revises: d4e9f2a6c801
Create Date: 2026-10-21 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e5a1b7c3d902"
down_revision = "d4e9f2a6c801"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "INSERT INTO notify.notification_provider VALUES('BC_NOTIFY_SMS','Delivery by BC Notify SMS service', false)"
    )


def downgrade():
    op.execute("DELETE FROM notify.notification_provider WHERE code='BC_NOTIFY_SMS'")
