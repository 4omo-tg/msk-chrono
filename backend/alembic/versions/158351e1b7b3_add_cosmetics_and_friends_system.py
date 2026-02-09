"""Add cosmetics and friends system

Revision ID: 158351e1b7b3
Revises: 1ef808ebc3d1
Create Date: 2025-02-07
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '158351e1b7b3'
down_revision = 'telegram_auth_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create title table
    op.create_table('title',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('color', sa.String(), nullable=True, server_default='amber'),
        sa.Column('rarity', sa.String(), nullable=True, server_default='common'),
        sa.Column('unlock_type', sa.String(), nullable=False),
        sa.Column('unlock_value', sa.String(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_title_id'), 'title', ['id'], unique=False)
    op.create_index(op.f('ix_title_code'), 'title', ['code'], unique=True)

    # Create profileframe table
    op.create_table('profileframe',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('css_class', sa.String(), nullable=True),
        sa.Column('rarity', sa.String(), nullable=True, server_default='common'),
        sa.Column('unlock_type', sa.String(), nullable=False),
        sa.Column('unlock_value', sa.String(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_profileframe_id'), 'profileframe', ['id'], unique=False)
    op.create_index(op.f('ix_profileframe_code'), 'profileframe', ['code'], unique=True)

    # Create badge table
    op.create_table('badge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('icon', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=True, server_default='amber'),
        sa.Column('rarity', sa.String(), nullable=True, server_default='common'),
        sa.Column('unlock_type', sa.String(), nullable=False),
        sa.Column('unlock_value', sa.String(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_badge_id'), 'badge', ['id'], unique=False)
    op.create_index(op.f('ix_badge_code'), 'badge', ['code'], unique=True)

    # Create user_title table
    op.create_table('user_title',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['title_id'], ['title.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_title_id'), 'user_title', ['id'], unique=False)
    op.create_index(op.f('ix_user_title_user_id'), 'user_title', ['user_id'], unique=False)

    # Create user_frame table
    op.create_table('user_frame',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('frame_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['frame_id'], ['profileframe.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_frame_id'), 'user_frame', ['id'], unique=False)
    op.create_index(op.f('ix_user_frame_user_id'), 'user_frame', ['user_id'], unique=False)

    # Create user_badge table
    op.create_table('user_badge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('badge_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['badge_id'], ['badge.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_badge_id'), 'user_badge', ['id'], unique=False)
    op.create_index(op.f('ix_user_badge_user_id'), 'user_badge', ['user_id'], unique=False)

    # Create friend_request table
    op.create_table('friend_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_user_id', sa.Integer(), nullable=False),
        sa.Column('to_user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['from_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('from_user_id', 'to_user_id', name='unique_friend_request')
    )
    op.create_index(op.f('ix_friend_request_id'), 'friend_request', ['id'], unique=False)
    op.create_index(op.f('ix_friend_request_from_user_id'), 'friend_request', ['from_user_id'], unique=False)
    op.create_index(op.f('ix_friend_request_to_user_id'), 'friend_request', ['to_user_id'], unique=False)

    # Create friendship table
    op.create_table('friendship',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('friend_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('nickname', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['friend_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'friend_id', name='unique_friendship')
    )
    op.create_index(op.f('ix_friendship_id'), 'friendship', ['id'], unique=False)
    op.create_index(op.f('ix_friendship_user_id'), 'friendship', ['user_id'], unique=False)
    op.create_index(op.f('ix_friendship_friend_id'), 'friendship', ['friend_id'], unique=False)

    # Add new columns to user table
    op.add_column('user', sa.Column('display_name', sa.String(), nullable=True))
    op.add_column('user', sa.Column('avatar_url', sa.String(), nullable=True))
    op.add_column('user', sa.Column('equipped_title_id', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('equipped_frame_id', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('equipped_badge_ids', sa.String(), nullable=True))
    op.add_column('user', sa.Column('profile_background', sa.String(), nullable=True, server_default='default'))
    op.add_column('user', sa.Column('total_distance_km', sa.Float(), nullable=True, server_default='0'))
    op.add_column('user', sa.Column('total_time_minutes', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('user', sa.Column('streak_days', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('user', sa.Column('last_activity_date', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('reputation', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('user', sa.Column('profile_visibility', sa.String(), nullable=True, server_default='public'))
    op.add_column('user', sa.Column('show_on_leaderboard', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('user', sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True))
    
    op.create_foreign_key('fk_user_title', 'user', 'title', ['equipped_title_id'], ['id'])
    op.create_foreign_key('fk_user_frame', 'user', 'profileframe', ['equipped_frame_id'], ['id'])


def downgrade() -> None:
    # Remove foreign keys from user
    op.drop_constraint('fk_user_title', 'user', type_='foreignkey')
    op.drop_constraint('fk_user_frame', 'user', type_='foreignkey')
    
    # Remove columns from user
    op.drop_column('user', 'created_at')
    op.drop_column('user', 'show_on_leaderboard')
    op.drop_column('user', 'profile_visibility')
    op.drop_column('user', 'reputation')
    op.drop_column('user', 'last_activity_date')
    op.drop_column('user', 'streak_days')
    op.drop_column('user', 'total_time_minutes')
    op.drop_column('user', 'total_distance_km')
    op.drop_column('user', 'profile_background')
    op.drop_column('user', 'equipped_badge_ids')
    op.drop_column('user', 'equipped_frame_id')
    op.drop_column('user', 'equipped_title_id')
    op.drop_column('user', 'avatar_url')
    op.drop_column('user', 'display_name')
    
    # Drop tables
    op.drop_index(op.f('ix_friendship_friend_id'), table_name='friendship')
    op.drop_index(op.f('ix_friendship_user_id'), table_name='friendship')
    op.drop_index(op.f('ix_friendship_id'), table_name='friendship')
    op.drop_table('friendship')
    
    op.drop_index(op.f('ix_friend_request_to_user_id'), table_name='friend_request')
    op.drop_index(op.f('ix_friend_request_from_user_id'), table_name='friend_request')
    op.drop_index(op.f('ix_friend_request_id'), table_name='friend_request')
    op.drop_table('friend_request')
    
    op.drop_index(op.f('ix_user_badge_user_id'), table_name='user_badge')
    op.drop_index(op.f('ix_user_badge_id'), table_name='user_badge')
    op.drop_table('user_badge')
    
    op.drop_index(op.f('ix_user_frame_user_id'), table_name='user_frame')
    op.drop_index(op.f('ix_user_frame_id'), table_name='user_frame')
    op.drop_table('user_frame')
    
    op.drop_index(op.f('ix_user_title_user_id'), table_name='user_title')
    op.drop_index(op.f('ix_user_title_id'), table_name='user_title')
    op.drop_table('user_title')
    
    op.drop_index(op.f('ix_badge_code'), table_name='badge')
    op.drop_index(op.f('ix_badge_id'), table_name='badge')
    op.drop_table('badge')
    
    op.drop_index(op.f('ix_profileframe_code'), table_name='profileframe')
    op.drop_index(op.f('ix_profileframe_id'), table_name='profileframe')
    op.drop_table('profileframe')
    
    op.drop_index(op.f('ix_title_code'), table_name='title')
    op.drop_index(op.f('ix_title_id'), table_name='title')
    op.drop_table('title')
