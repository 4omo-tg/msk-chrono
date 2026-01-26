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
    
    # Seed default achievements - разнообразные ачивки
    op.execute("""
        INSERT INTO achievement (code, title, description, icon, xp_reward, condition_type, condition_value) VALUES
        -- Точки (points)
        ('first_step', 'Первый шаг', 'Посетите первую достопримечательность Москвы', 'Footprints', 25, 'points', 1),
        ('curious', 'Любопытный турист', 'Посетите 3 точки на маршрутах', 'Target', 30, 'points', 3),
        ('explorer', 'Исследователь', 'Откройте для себя 5 исторических мест', 'Compass', 50, 'points', 5),
        ('historian', 'Знаток истории', 'Посетите 10 достопримечательностей', 'BookOpen', 75, 'points', 10),
        ('veteran', 'Ветеран прогулок', 'Посетите 20 точек по всей Москве', 'Medal', 100, 'points', 20),
        ('moscow_expert', 'Эксперт по Москве', 'Посетите 50 исторических мест', 'Star', 200, 'points', 50),
        
        -- Маршруты (routes)
        ('pathfinder', 'Следопыт', 'Завершите свой первый маршрут полностью', 'Flag', 100, 'routes', 1),
        ('wanderer', 'Странник', 'Пройдите 2 разных маршрута', 'Route', 120, 'routes', 2),
        ('master', 'Мастер маршрутов', 'Завершите 3 маршрута', 'Trophy', 150, 'routes', 3),
        ('city_walker', 'Городской ходок', 'Пройдите 5 маршрутов по Москве', 'Mountain', 250, 'routes', 5),
        
        -- Уровни (level)
        ('rising_star', 'Восходящая звезда', 'Достигните 2 уровня', 'Zap', 50, 'level', 2),
        ('experienced', 'Опытный', 'Достигните 3 уровня', 'Flame', 75, 'level', 3),
        ('legend', 'Легенда Москвы', 'Достигните 5 уровня', 'Crown', 200, 'level', 5),
        ('mythical', 'Мифический статус', 'Достигните 10 уровня', 'Gem', 500, 'level', 10),
        
        -- Квизы (quizzes)
        ('quiz_starter', 'Начинающий эрудит', 'Правильно ответьте на первый квиз', 'Sparkles', 25, 'quizzes', 1),
        ('quiz_lover', 'Любитель загадок', 'Пройдите 5 квизов успешно', 'BookOpen', 75, 'quizzes', 5),
        ('quiz_master', 'Мастер викторин', 'Ответьте правильно на 10 квизов', 'Award', 150, 'quizzes', 10)
    """)


def downgrade() -> None:
    """Drop achievement tables."""
    op.drop_table('user_achievement')
    op.drop_table('achievement')
