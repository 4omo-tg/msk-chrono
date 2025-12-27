"""add cascade delete to user_progress

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-12-27 20:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add CASCADE delete to route_id foreign key in user_progress."""
    # Drop existing constraint
    op.drop_constraint('user_progress_route_id_fkey', 'user_progress', type_='foreignkey')
    
    # Re-create with CASCADE
    op.create_foreign_key(
        'user_progress_route_id_fkey',
        'user_progress', 'route',
        ['route_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Revert CASCADE delete."""
    # Drop CASCADE constraint
    op.drop_constraint('user_progress_route_id_fkey', 'user_progress', type_='foreignkey')
    
    # Re-create without CASCADE
    op.create_foreign_key(
        'user_progress_route_id_fkey',
        'user_progress', 'route',
        ['route_id'], ['id']
    )
