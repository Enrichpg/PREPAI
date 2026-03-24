revision = '002_add_events_table'
down_revision = '001'
"""
Add events table
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'events',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('external_id', sa.String, unique=True, nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('start_time', sa.DateTime, nullable=False),
        sa.Column('end_time', sa.DateTime, nullable=False),
        sa.Column('zone_id', sa.Integer, sa.ForeignKey('zones.id')),
        sa.Column('venue', sa.String),
        sa.Column('latitude', sa.Float),
        sa.Column('longitude', sa.Float),
    )

def downgrade():
    op.drop_table('events')
