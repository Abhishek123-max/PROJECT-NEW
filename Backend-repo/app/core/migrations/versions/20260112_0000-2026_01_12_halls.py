"""Remove hall_type and add hall_capacity to halls table

Revision ID: 2026_01_12_halls
Revises: 20260108_1736_add_hotel_fields
Create Date: 2026-01-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2026_01_12_halls'
down_revision = '20260108_1736_add_hotel_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove hall_type column and add hall_capacity column to halls table."""
    # Drop hall_type column
    op.drop_column('halls', 'hall_type')
    
    # Add hall_capacity column
    op.add_column('halls', sa.Column('hall_capacity', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Revert changes: remove hall_capacity and restore hall_type."""
    # Drop hall_capacity column
    op.drop_column('halls', 'hall_capacity')
    
    # Add hall_type column back
    op.add_column('halls', sa.Column('hall_type', sa.String(length=50), nullable=True))
