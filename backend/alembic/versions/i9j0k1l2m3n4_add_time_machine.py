"""Add time machine feature (chrono_crystals + time_photo table)

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2025-02-10
"""
from alembic import op
import sqlalchemy as sa

revision = 'i9j0k1l2m3n4'
down_revision = 'h8i9j0k1l2m3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User: add chrono_crystals balance
    op.add_column('user', sa.Column('chrono_crystals', sa.Integer(), nullable=False, server_default='5'))

    # Time Photo table
    op.create_table(
        'time_photo',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('original_image_url', sa.String(), nullable=False),
        sa.Column('result_image_url', sa.String(), nullable=True),
        sa.Column('target_year', sa.Integer(), nullable=False),
        sa.Column('apply_era_style', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('style_applied', sa.String(), nullable=True),
        sa.Column('prompt_used', sa.String(), nullable=True),
        sa.Column('geminigen_uuid', sa.String(), nullable=True),
        sa.Column('status', sa.String(), server_default='pending', nullable=False),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('cost', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('time_photo')
    op.drop_column('user', 'chrono_crystals')
