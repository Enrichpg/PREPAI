"""
Add ingestion_metadata column to data_ingestion_logs
"""
from alembic import op
import sqlalchemy as sa

revision = '005_add_ingestion_metadata'
down_revision = '8fb1d678929e'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('data_ingestion_logs', sa.Column('ingestion_metadata', sa.JSON))

def downgrade():
    op.drop_column('data_ingestion_logs', 'ingestion_metadata')
