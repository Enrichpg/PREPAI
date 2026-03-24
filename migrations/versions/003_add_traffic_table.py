"""
Add traffic_data table
"""
revision = '003_add_traffic_table'
down_revision = '002_add_events_table'
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'traffic_data',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('zone_id', sa.Integer),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('traffic_level', sa.Float, nullable=False),
        sa.Column('description', sa.String),
    )

def downgrade():
    op.drop_table('traffic_data')
