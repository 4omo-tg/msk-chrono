"""add_quiz_tables

Revision ID: 9e09e7734423
Revises: c3d4e5f6g7h8
Create Date: 2026-01-26 19:48:57.339831

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '9e09e7734423'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('quiz',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('poi_id', sa.Integer(), nullable=False),
        sa.Column('question', sa.String(), nullable=False),
        sa.Column('option_a', sa.String(), nullable=False),
        sa.Column('option_b', sa.String(), nullable=False),
        sa.Column('option_c', sa.String(), nullable=False),
        sa.Column('option_d', sa.String(), nullable=False),
        sa.Column('correct_answer', sa.String(), nullable=False),
        sa.Column('xp_reward', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['poi_id'], ['point_of_interest.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiz_id'), 'quiz', ['id'], unique=False)
    op.create_index(op.f('ix_quiz_poi_id'), 'quiz', ['poi_id'], unique=False)
    
    op.create_table('user_quiz_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['quiz_id'], ['quiz.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_quiz_progress_id'), 'user_quiz_progress', ['id'], unique=False)
    op.create_index(op.f('ix_user_quiz_progress_quiz_id'), 'user_quiz_progress', ['quiz_id'], unique=False)
    op.create_index(op.f('ix_user_quiz_progress_user_id'), 'user_quiz_progress', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_quiz_progress_user_id'), table_name='user_quiz_progress')
    op.drop_index(op.f('ix_user_quiz_progress_quiz_id'), table_name='user_quiz_progress')
    op.drop_index(op.f('ix_user_quiz_progress_id'), table_name='user_quiz_progress')
    op.drop_table('user_quiz_progress')
    op.drop_index(op.f('ix_quiz_poi_id'), table_name='quiz')
    op.drop_index(op.f('ix_quiz_id'), table_name='quiz')
    op.drop_table('quiz')
