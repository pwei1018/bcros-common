"""add bc_notify provider

Revision ID: a1b2c3d4e5f6
Revises: 5b8087f8b7e3
Create Date: 2026-07-03 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "5b8087f8b7e3"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("INSERT INTO notify.notification_provider VALUES('BC_NOTIFY','Delivery by BC Notify service', false)")
    op.execute(
        "INSERT INTO notify.notification_provider VALUES('BC_NOTIFY_HOUSING','Delivery by BC Notify Housing service', false)"
    )


def downgrade():
    op.execute("DELETE FROM notify.notification_provider WHERE code='BC_NOTIFY'")
    op.execute("DELETE FROM notify.notification_provider WHERE code='BC_NOTIFY_HOUSING'")
