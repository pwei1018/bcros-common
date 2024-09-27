"""0003_search

Revision ID: 43a86e041c8a
Revises: 89e4f7fdd132
Create Date: 2024-09-09 12:03:39.556360

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '43a86e041c8a'
down_revision = '89e4f7fdd132'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('document_class', postgresql.ENUM('COOP', 'CORP', 'FIRM', 'LP_LLP', 'MHR', 'NR', 'OTHER', 'PPR', 'SOCIETY', 'XP', name='documentclass'), nullable=False))
        batch_op.add_column(sa.Column('description', sa.String(length=1000), nullable=True))
        batch_op.create_index(batch_op.f('ix_documents_consumer_filename'), ['consumer_filename'], unique=False)
        batch_op.create_index(batch_op.f('ix_documents_document_class'), ['document_class'], unique=False)
        batch_op.create_index(batch_op.f('ix_documents_document_type'), ['document_type'], unique=False)
        batch_op.create_foreign_key(None, 'document_classes', ['document_class'], ['document_class'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_documents_document_type'))
        batch_op.drop_index(batch_op.f('ix_documents_document_class'))
        batch_op.drop_index(batch_op.f('ix_documents_consumer_filename'))
        batch_op.drop_column('document_class')
        batch_op.drop_column('description')

    # ### end Alembic commands ###