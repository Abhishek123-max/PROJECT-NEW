"""Add profile fields to users

Revision ID: 20260128_add_user_profile_fields
Revises: 67f1bf31371f
Create Date: 2026-01-28 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260128_add_user_profile_fields"
down_revision = "67f1bf31371f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("annual_salary", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("joining_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("department", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("street_address", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("city", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("state", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("pin_code", sa.String(length=10), nullable=True))
    op.add_column("users", sa.Column("country", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("emergency_contact_name", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("emergency_contact_phone", sa.String(length=20), nullable=True))
    op.add_column(
        "users",
        sa.Column("emergency_contact_relationship", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "emergency_contact_relationship")
    op.drop_column("users", "emergency_contact_phone")
    op.drop_column("users", "emergency_contact_name")
    op.drop_column("users", "country")
    op.drop_column("users", "pin_code")
    op.drop_column("users", "state")
    op.drop_column("users", "city")
    op.drop_column("users", "street_address")
    op.drop_column("users", "department")
    op.drop_column("users", "joining_date")
    op.drop_column("users", "annual_salary")
    op.drop_column("users", "date_of_birth")