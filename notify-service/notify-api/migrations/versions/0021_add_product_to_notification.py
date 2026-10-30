"""Add optional product metadata to notifications and history.

Revision ID: a61d9c4e7f20
Revises: f6b2c8d4e013
Create Date: 2026-10-28 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a61d9c4e7f20"
down_revision = "f6b2c8d4e013"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("notification", sa.Column("product", sa.String(length=50), nullable=True))
    op.add_column("notification_history", sa.Column("product", sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column("notification_history", "product")
    op.drop_column("notification", "product")