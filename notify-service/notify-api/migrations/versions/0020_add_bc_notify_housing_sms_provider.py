"""add bc_notify_housing_sms provider

Revision ID: f6b2c8d4e013
Revises: e5a1b7c3d902
Create Date: 2026-10-21 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f6b2c8d4e013"
down_revision = "e5a1b7c3d902"
branch_labels = None
depends_on = None


def upgrade():
    # Provider codes longer than 15 chars must fit the referencing columns too.
    op.execute("ALTER TABLE notify.notification ALTER COLUMN provider_code TYPE VARCHAR(50);")
    op.execute("ALTER TABLE notify.notification_history ALTER COLUMN provider_code TYPE VARCHAR(50);")
    op.execute(
        "INSERT INTO notify.notification_provider VALUES"
        "('BC_NOTIFY_HOUSING_SMS','Delivery by BC Notify Housing SMS service', false)"
    )


def downgrade():
    op.execute("DELETE FROM notify.notification_provider WHERE code='BC_NOTIFY_HOUSING_SMS'")
