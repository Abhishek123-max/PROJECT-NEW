"""
Alembic migration script to support many-to-many assignees for tables.
- Drops the assigned_to column from tables
- Creates the table_assignees association table
"""

# revision identifiers, used by Alembic.
revision = '20260108_many_to_many_assignees'
down_revision = '93a01cd00e4f'  # Set this to the previous migration's revision id if you have one
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Drop the assigned_to column from tables
    with op.batch_alter_table('tables') as batch_op:
        batch_op.drop_column('assigned_to')

    # Create the association table for assignees
    op.create_table(
        'table_assignees',
        sa.Column('table_id', sa.Integer(), sa.ForeignKey('tables.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    )

def downgrade():
    # Drop the association table
    op.drop_table('table_assignees')

    # Add the assigned_to column back to tables
    with op.batch_alter_table('tables') as batch_op:
        batch_op.add_column(sa.Column('assigned_to', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
