"""Add hotel fields to branches table

Revision ID: 20260108_1736_add_hotel_fields
Revises: 20260108_many_to_many_assignees
Create Date: 2026-01-08 17:36:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260108_1736_add_hotel_fields'
down_revision: Union[str, None] = '20260108_many_to_many_assignees'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add all hotel fields to branches table."""
    # Add all fields from hotels table to branches table
    op.add_column('branches', sa.Column('owner_name', sa.String(length=100), nullable=True))
    op.add_column('branches', sa.Column('gst_number', sa.String(length=20), nullable=True))
    op.add_column('branches', sa.Column('country', sa.String(length=100), nullable=True))
    op.add_column('branches', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('branches', sa.Column('longitude', sa.Float(), nullable=True))
    op.add_column('branches', sa.Column('subscription_plan', sa.String(length=50), nullable=True))
    op.add_column('branches', sa.Column('business_type', sa.String(length=100), nullable=True))
    op.add_column('branches', sa.Column('logo_url', sa.String(length=255), nullable=True))
    op.add_column('branches', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('branches', sa.Column('fssai_number', sa.String(length=100), nullable=True))
    op.add_column('branches', sa.Column('tin_number', sa.String(length=100), nullable=True))
    op.add_column('branches', sa.Column('professional_tax_reg_number', sa.String(length=100), nullable=True))
    op.add_column('branches', sa.Column('trade_license_number', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Remove hotel fields from branches table."""
    op.drop_column('branches', 'trade_license_number')
    op.drop_column('branches', 'professional_tax_reg_number')
    op.drop_column('branches', 'tin_number')
    op.drop_column('branches', 'fssai_number')
    op.drop_column('branches', 'description')
    op.drop_column('branches', 'logo_url')
    op.drop_column('branches', 'business_type')
    op.drop_column('branches', 'subscription_plan')
    op.drop_column('branches', 'longitude')
    op.drop_column('branches', 'latitude')
    op.drop_column('branches', 'country')
    op.drop_column('branches', 'gst_number')
    op.drop_column('branches', 'owner_name')
