"""Add achievements tables

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2025-01-26 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create achievement tables."""
    # Achievement definitions
    op.create_table(
        'achievement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('icon', sa.String(), nullable=False, server_default='Award'),
        sa.Column('xp_reward', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('condition_type', sa.String(), nullable=False),
        sa.Column('condition_value', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_achievement_id', 'achievement', ['id'])
    op.create_index('ix_achievement_code', 'achievement', ['code'], unique=True)
    
    # User achievements (many-to-many)
    op.create_table(
        'user_achievement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievement.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_achievement_id', 'user_achievement', ['id'])
    op.create_index('ix_user_achievement_user_id', 'user_achievement', ['user_id'])
    
    # Seed default achievements
    op.execute("""
        INSERT INTO achievement (code, title, description, icon, xp_reward, condition_type, condition_value) VALUES
        ('first_step', 'Первый шаг', 'Посетите первую точку', 'MapPin', 25, 'points', 1),
        ('explorer', 'Исследователь', 'Посетите 5 точек', 'Compass', 50, 'points', 5),
        ('pathfinder', 'Следопыт', 'Завершите первый маршрут', 'Route', 100, 'routes', 1),
        ('veteran', 'Ветеран', 'Посетите 10 точек', 'Star', 75, 'points', 10),
        ('master', 'Мастер', 'Завершите 3 маршрута', 'Trophy', 150, 'routes', 3),
        ('legend', 'Легенда', 'Достигните 5 уровня', 'Award', 200, 'level', 5)
    """)


def downgrade() -> None:
    """Drop achievement tables."""
    op.drop_table('user_achievement')
    op.drop_table('achievement')
