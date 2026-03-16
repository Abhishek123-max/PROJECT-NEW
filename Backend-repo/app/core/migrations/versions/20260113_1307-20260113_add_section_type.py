"""Add section_type to sections table

Revision ID: 20260113_add_section_type
Revises: 20260112_0000-2026_01_12_halls
Create Date: 2026-01-13 13:07:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260113_add_section_type'
down_revision = '2026_01_12_halls'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sections', sa.Column('section_type', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('sections', 'section_type')

