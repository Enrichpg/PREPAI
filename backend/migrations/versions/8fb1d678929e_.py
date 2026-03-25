"""empty message

Revision ID: 8fb1d678929e
Revises: 004_add_ingestion_metadata_to_data_ingestion_logs, 004_ingestion_metadata
Create Date: 2026-03-18 12:05:23.612207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '8fb1d678929e'
down_revision: str = '003_add_traffic_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
