"""add gallery and panorama fields to POI

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2025-01-26 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, Sequence[str], None] = '9e09e7734423'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add gallery and panorama fields to point_of_interest."""
    # Gallery arrays for multiple images
    op.add_column('point_of_interest', 
        sa.Column('historic_images', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('point_of_interest', 
        sa.Column('modern_images', postgresql.ARRAY(sa.String()), nullable=True))
    
    # Panorama URLs
    op.add_column('point_of_interest', 
        sa.Column('historic_panorama_url', sa.String(), nullable=True))
    op.add_column('point_of_interest', 
        sa.Column('modern_panorama_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove gallery and panorama fields."""
    op.drop_column('point_of_interest', 'modern_panorama_url')
    op.drop_column('point_of_interest', 'historic_panorama_url')
    op.drop_column('point_of_interest', 'modern_images')
    op.drop_column('point_of_interest', 'historic_images')
