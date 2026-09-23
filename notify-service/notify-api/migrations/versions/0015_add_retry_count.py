"""add retry_count to notification

Revision ID: 8a1c4f2d9b3e
Revises: 5b8087f8b7e3
Create Date: 2026-09-22 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "8a1c4f2d9b3e"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "notification",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("notification", "retry_count")
