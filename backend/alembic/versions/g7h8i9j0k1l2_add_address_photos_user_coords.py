"""Add address to POI, poi_photo table, user coordinates

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2025-02-09
"""
from alembic import op
import sqlalchemy as sa

revision = 'g7h8i9j0k1l2'
down_revision = 'f6g7h8i9j0k1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # POI: add address
    op.add_column('point_of_interest', sa.Column('address', sa.String(), nullable=True))

    # User: add coordinates
    op.add_column('user', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('user', sa.Column('longitude', sa.Float(), nullable=True))

    # POI Photo table (photos by year)
    op.create_table(
        'poi_photo',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('poi_id', sa.Integer(), sa.ForeignKey('point_of_interest.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('year', sa.Integer(), nullable=False, index=True),
        sa.Column('image_url', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('poi_photo')
    op.drop_column('user', 'longitude')
    op.drop_column('user', 'latitude')
    op.drop_column('point_of_interest', 'address')
