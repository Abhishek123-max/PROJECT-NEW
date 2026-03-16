"""add unique constraint branch_id_floor_name

Revision ID: 67f1bf31371f
Revises: 20260113_add_section_type
Create Date: 2026-01-14 15:45:36.758698

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67f1bf31371f'
down_revision: Union[str, None] = '20260113_add_section_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_branch_floor_name",
        "floors",
        ["branch_id", "floor_name"],
    )

def downgrade() -> None:
    op.drop_constraint(
        "uq_branch_floor_name",
        "floors",
        type_="unique",
    )