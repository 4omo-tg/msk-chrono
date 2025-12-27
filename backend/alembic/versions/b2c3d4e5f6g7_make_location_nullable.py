"""make location nullable

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-27 20:26:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make location column nullable."""
    # Make location nullable since we're using latitude/longitude now
    op.alter_column('point_of_interest', 'location', nullable=True)


def downgrade() -> None:
    """Revert location column to not nullable."""
    # First populate any NULL locations before making it non-nullable again
    op.execute("""
        UPDATE point_of_interest
        SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        WHERE location IS NULL
    """)
    op.alter_column('point_of_interest', 'location', nullable=False)
