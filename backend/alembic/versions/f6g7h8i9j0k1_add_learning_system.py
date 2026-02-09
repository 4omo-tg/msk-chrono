"""Add learning system

Revision ID: f6g7h8i9j0k1
Revises: 158351e1b7b3
Create Date: 2025-02-08
"""
from alembic import op
import sqlalchemy as sa


revision = 'f6g7h8i9j0k1'
down_revision = '158351e1b7b3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('learning_module',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True, server_default='BookOpen'),
        sa.Column('order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learning_module_id'), 'learning_module', ['id'], unique=False)

    op.create_table('learning_lesson',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('xp_reward', sa.Integer(), nullable=True, server_default='10'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['learning_module.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learning_lesson_id'), 'learning_lesson', ['id'], unique=False)
    op.create_index(op.f('ix_learning_lesson_module_id'), 'learning_lesson', ['module_id'], unique=False)

    op.create_table('learning_question',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(), nullable=False, server_default='multiple_choice'),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('correct_answer', sa.String(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['lesson_id'], ['learning_lesson.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learning_question_id'), 'learning_question', ['id'], unique=False)
    op.create_index(op.f('ix_learning_question_lesson_id'), 'learning_question', ['lesson_id'], unique=False)

    op.create_table('user_learning_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_xp', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('current_streak', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('daily_goal', sa.Integer(), nullable=True, server_default='10'),
        sa.Column('last_activity_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('league', sa.String(), nullable=True, server_default='bronze'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_learning_progress_id'), 'user_learning_progress', ['id'], unique=False)
    op.create_index(op.f('ix_user_learning_progress_user_id'), 'user_learning_progress', ['user_id'], unique=False)

    op.create_table('user_lesson_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('best_score', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('attempts', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['lesson_id'], ['learning_lesson.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_lesson_progress_id'), 'user_lesson_progress', ['id'], unique=False)
    op.create_index(op.f('ix_user_lesson_progress_user_id'), 'user_lesson_progress', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_lesson_progress_lesson_id'), 'user_lesson_progress', ['lesson_id'], unique=False)

    op.create_table('user_question_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['learning_question.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_question_history_id'), 'user_question_history', ['id'], unique=False)
    op.create_index(op.f('ix_user_question_history_user_id'), 'user_question_history', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_question_history_question_id'), 'user_question_history', ['question_id'], unique=False)

    op.create_table('learning_session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('xp_earned', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['lesson_id'], ['learning_lesson.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learning_session_id'), 'learning_session', ['id'], unique=False)
    op.create_index(op.f('ix_learning_session_user_id'), 'learning_session', ['user_id'], unique=False)
    op.create_index(op.f('ix_learning_session_lesson_id'), 'learning_session', ['lesson_id'], unique=False)


def downgrade() -> None:
    op.drop_table('learning_session')
    op.drop_table('user_question_history')
    op.drop_table('user_lesson_progress')
    op.drop_table('user_learning_progress')
    op.drop_table('learning_question')
    op.drop_table('learning_lesson')
    op.drop_table('learning_module')
