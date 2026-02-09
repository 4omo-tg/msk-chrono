"""add_telegram_auth_fields

Revision ID: telegram_auth_001
Revises: 
Create Date: 2025-02-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'telegram_auth_001'
down_revision: Union[str, None] = 'e5f6g7h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add telegram fields to user table
    op.add_column('user', sa.Column('telegram_id', sa.BigInteger(), nullable=True))
    op.add_column('user', sa.Column('telegram_username', sa.String(), nullable=True))
    op.add_column('user', sa.Column('telegram_first_name', sa.String(), nullable=True))
    op.add_column('user', sa.Column('telegram_photo_url', sa.String(), nullable=True))
    op.create_index('ix_user_telegram_id', 'user', ['telegram_id'], unique=True)
    
    # Make email and password nullable for telegram-only users
    op.alter_column('user', 'email', existing_type=sa.String(), nullable=True)
    op.alter_column('user', 'hashed_password', existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.drop_index('ix_user_telegram_id', table_name='user')
    op.drop_column('user', 'telegram_photo_url')
    op.drop_column('user', 'telegram_first_name')
    op.drop_column('user', 'telegram_username')
    op.drop_column('user', 'telegram_id')
    op.alter_column('user', 'email', existing_type=sa.String(), nullable=False)
    op.alter_column('user', 'hashed_password', existing_type=sa.String(), nullable=False)
