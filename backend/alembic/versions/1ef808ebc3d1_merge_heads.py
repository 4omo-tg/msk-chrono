"""merge heads

Revision ID: 1ef808ebc3d1
Revises: telegram_auth_001, add_tg_auth_sessions
Create Date: 2026-02-07 18:06:38.609825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ef808ebc3d1'
down_revision: Union[str, Sequence[str], None] = ('telegram_auth_001', 'add_tg_auth_sessions')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
