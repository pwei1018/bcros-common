"""add new provider

Revision ID: d6a8ffda6b9c
Revises: fc3eb17e9773
Create Date: 2025-01-31 16:20:44.807772

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd6a8ffda6b9c'
down_revision = 'fc3eb17e9773'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "INSERT INTO notification_provider VALUES('HOUSING','Delivery by GC Notify Housing service', false)"
    )


def downgrade():
    op.execute("DELETE notification_provider WHERE code='HOUSING'")
