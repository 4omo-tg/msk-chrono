"""add lat lon to poi

Revision ID: a1b2c3d4e5f6
Revises: 861a7610a375
Create Date: 2025-12-27 12:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '861a7610a375'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add latitude and longitude columns to point_of_interest table."""
    # Add the new columns
    op.add_column('point_of_interest', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('point_of_interest', sa.Column('longitude', sa.Float(), nullable=True))
    
    # Populate the new columns from the existing geometry column
    # Using PostGIS functions: ST_Y for latitude, ST_X for longitude
    op.execute("""
        UPDATE point_of_interest
        SET latitude = ST_Y(location),
            longitude = ST_X(location)
    """)
    
    # Make the columns non-nullable now that they have values
    op.alter_column('point_of_interest', 'latitude', nullable=False)
    op.alter_column('point_of_interest', 'longitude', nullable=False)


def downgrade() -> None:
    """Remove latitude and longitude columns from point_of_interest table."""
    op.drop_column('point_of_interest', 'longitude')
    op.drop_column('point_of_interest', 'latitude')
