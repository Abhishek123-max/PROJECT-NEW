"""Create initial tables

Revision ID: 001
Revises: 
Create Date: 2025-09-05 11:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # 1. Create roles table first (no dependencies)
    op.create_table('roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default='{}'),
        sa.Column('can_create_roles', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default='[]'),
        sa.Column('default_features', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_roles'))
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_level'), 'roles', ['level'], unique=False)
    op.create_index('ix_roles_level_active', 'roles', ['level', 'is_active'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    op.create_index('ix_roles_name_active', 'roles', ['name'], unique=False, postgresql_where='is_active = true')

    # 2. Create users table (depends on roles, but without foreign key constraints to hotels/branches/zones yet)
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('hotel_id', sa.Integer(), nullable=True),
        sa.Column('branch_id', sa.Integer(), nullable=True),
        sa.Column('zone_id', sa.Integer(), nullable=True),
        sa.Column('feature_toggles', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default='{}'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_users_role_id_roles')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_users_created_by_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index(op.f('ix_users_role_id'), 'users', ['role_id'], unique=False)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_created_by'), 'users', ['created_by'], unique=False)
    op.create_index('ix_users_created_at_desc', 'users', ['created_at'], unique=False, postgresql_using='btree')
    op.create_index('ix_users_active_role', 'users', ['is_active', 'role_id'], unique=False)
    op.create_index('ix_users_active_email', 'users', ['email'], unique=False, postgresql_where='is_active = true')

    # 3. Create hotels table (depends on users)
    op.create_table('hotels',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('owner_name', sa.String(length=100), nullable=False),
        sa.Column('gst_number', sa.String(length=15), nullable=True),
        sa.Column('pan_number', sa.String(length=10), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False, default='India'),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('phone', sa.String(length=15), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('subscription_plan', sa.String(length=50), nullable=False, default='basic'),
        sa.Column('subscription_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, default='Asia/Kolkata'),
        sa.Column('currency', sa.String(length=3), nullable=False, default='INR'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_hotels_created_by_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_hotels'))
    )
    op.create_index(op.f('ix_hotels_id'), 'hotels', ['id'], unique=False)
    op.create_index(op.f('ix_hotels_name'), 'hotels', ['name'], unique=False)
    op.create_index(op.f('ix_hotels_city'), 'hotels', ['city'], unique=False)
    op.create_index(op.f('ix_hotels_state'), 'hotels', ['state'], unique=False)
    op.create_index(op.f('ix_hotels_gst_number'), 'hotels', ['gst_number'], unique=False)
    op.create_index(op.f('ix_hotels_is_active'), 'hotels', ['is_active'], unique=False)
    op.create_index(op.f('ix_hotels_subscription_plan'), 'hotels', ['subscription_plan'], unique=False)
    op.create_index(op.f('ix_hotels_created_at'), 'hotels', ['created_at'], unique=False)
    op.create_index(op.f('ix_hotels_created_by'), 'hotels', ['created_by'], unique=False)
    op.create_index('ix_hotels_active_subscription', 'hotels', ['is_active', 'subscription_plan'], unique=False)
    op.create_index('ix_hotels_owner_name', 'hotels', ['owner_name'], unique=False)
    op.create_index('ix_hotels_gst_active', 'hotels', ['gst_number'], unique=False, postgresql_where='is_active = true')

    # 4. Create branches table (depends on hotels)
    op.create_table('branches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hotel_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=True),
        sa.Column('gst_number', sa.String(length=15), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('phone', sa.String(length=15), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('manager_name', sa.String(length=100), nullable=True),
        sa.Column('bank_details', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default='{}'),
        sa.Column('seating_capacity', sa.Integer(), nullable=True),
        sa.Column('operating_hours', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], name=op.f('fk_branches_hotel_id_hotels')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_branches')),
        sa.UniqueConstraint('hotel_id', 'code', name='uq_branches_hotel_code')
    )
    op.create_index(op.f('ix_branches_id'), 'branches', ['id'], unique=False)
    op.create_index(op.f('ix_branches_hotel_id'), 'branches', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_branches_city'), 'branches', ['city'], unique=False)
    op.create_index(op.f('ix_branches_is_active'), 'branches', ['is_active'], unique=False)
    op.create_index('ix_branches_hotel_active', 'branches', ['hotel_id', 'is_active'], unique=False)
    op.create_index('ix_branches_hotel_name', 'branches', ['hotel_id', 'name'], unique=False)

    # 5. Create zones table (depends on branches)
    op.create_table('zones',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('zone_type', sa.String(length=50), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name=op.f('fk_zones_branch_id_branches')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_zones')),
        sa.UniqueConstraint('branch_id', 'code', name='uq_zones_branch_code')
    )
    op.create_index(op.f('ix_zones_id'), 'zones', ['id'], unique=False)
    op.create_index(op.f('ix_zones_branch_id'), 'zones', ['branch_id'], unique=False)
    op.create_index(op.f('ix_zones_zone_type'), 'zones', ['zone_type'], unique=False)
    op.create_index(op.f('ix_zones_is_active'), 'zones', ['is_active'], unique=False)
    op.create_index('ix_zones_branch_active', 'zones', ['branch_id', 'is_active'], unique=False)
    op.create_index('ix_zones_branch_type', 'zones', ['branch_id', 'zone_type'], unique=False)

    # 5a. Create floors table (depends on branches)
    op.create_table(
        'floors',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('hotel_id', sa.Integer(), nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=False),
        sa.Column('floor_number', sa.Integer()),
        sa.Column('floor_name', sa.String(100)),
        sa.Column('floor_sequence', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),

        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id']),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id']),
        sa.UniqueConstraint('hotel_id', 'branch_id', 'floor_sequence', name='uq_floor_tenant')
)

    op.create_table(
        'floor_managers',
        sa.Column('id', sa.Integer(), primary_key=True),

        sa.Column('hotel_id', sa.Integer(), nullable=False),
        sa.Column('floor_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),

        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id']),
        sa.ForeignKeyConstraint(['floor_id'], ['floors.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),

        sa.UniqueConstraint(
            'hotel_id',
            'floor_id',
            'user_id',
            name='uq_floor_manager_tenant'
        )
)


    # 5b. Create sections table (depends on branches)
    op.create_table('sections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('branch_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('code', sa.String(length=10), nullable=True),
        sa.Column('section_type', sa.String(length=50), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_sections'))
    )
    op.create_index(op.f('ix_sections_id'), 'sections', ['id'], unique=False)
    op.create_index(op.f('ix_sections_branch_id'), 'sections', ['branch_id'], unique=False)

    # 6. Now add the missing foreign key constraints to users table
    op.create_foreign_key(op.f('fk_users_hotel_id_hotels'), 'users', 'hotels', ['hotel_id'], ['id'])
    op.create_foreign_key(op.f('fk_users_branch_id_branches'), 'users', 'branches', ['branch_id'], ['id'])
    op.create_foreign_key(op.f('fk_users_zone_id_zones'), 'users', 'zones', ['zone_id'], ['id'])

    # Add remaining indexes for users table
    op.create_index(op.f('ix_users_hotel_id'), 'users', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_users_branch_id'), 'users', ['branch_id'], unique=False)
    op.create_index(op.f('ix_users_zone_id'), 'users', ['zone_id'], unique=False)
    op.create_index('ix_users_hotel_branch', 'users', ['hotel_id', 'branch_id'], unique=False)
    op.create_index('ix_users_hotel_role', 'users', ['hotel_id', 'role_id'], unique=False)
    op.create_index('ix_users_branch_role', 'users', ['branch_id', 'role_id'], unique=False)
    op.create_index('ix_users_hotel_branch_role', 'users', ['hotel_id', 'branch_id', 'role_id'], unique=False)
    op.create_index('ix_users_active_hotel', 'users', ['hotel_id'], unique=False, postgresql_where='is_active = true')
    op.create_index('ix_users_active_branch', 'users', ['branch_id'], unique=False, postgresql_where='is_active = true')

    # 7. Create audit_logs table (depends on users, hotels, branches)
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('hotel_id', sa.Integer(), nullable=True),
        sa.Column('branch_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=36), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default='{}'),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('success', sa.String(length=20), nullable=False),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_audit_logs_user_id_users')),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], name=op.f('fk_audit_logs_target_user_id_users')),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], name=op.f('fk_audit_logs_hotel_id_hotels')),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name=op.f('fk_audit_logs_branch_id_branches')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_event_type'), 'audit_logs', ['event_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_hotel_id'), 'audit_logs', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_branch_id'), 'audit_logs', ['branch_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index('ix_audit_logs_timestamp_desc', 'audit_logs', ['timestamp'], unique=False, postgresql_using='btree')

    # 8. Create refresh_tokens table (depends on users)
    op.create_table('refresh_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('device_info', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default='{}'),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, default=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_reason', sa.String(length=100), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_refresh_tokens_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_refresh_tokens'))
    )
    op.create_index(op.f('ix_refresh_tokens_id'), 'refresh_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_expires_at'), 'refresh_tokens', ['expires_at'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_is_revoked'), 'refresh_tokens', ['is_revoked'], unique=False)


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop tables in reverse order
    op.drop_table('sections')
    op.drop_table('floors')
    op.drop_table('refresh_tokens')
    op.drop_table('audit_logs')
    op.drop_table('zones')
    op.drop_table('branches')
    op.drop_table('hotels')
    op.drop_table('users')
    op.drop_table('roles')