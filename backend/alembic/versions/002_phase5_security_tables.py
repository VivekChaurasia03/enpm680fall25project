"""Add Phase 5 security tables

Revision ID: 002
Revises: 001
Create Date: 2025-11-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create failed_login_attempts table
    op.create_table(
        'failed_login_attempts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('first_attempt', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_attempt', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_failed_login_attempts_user_email'), 'failed_login_attempts', ['user_email'], unique=False)
    op.create_index(op.f('ix_failed_login_attempts_last_attempt'), 'failed_login_attempts', ['last_attempt'], unique=False)
    
    # Create security_events table
    op.create_table(
        'security_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='severity'), nullable=False, server_default='LOW'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_events_event_type'), 'security_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_security_events_user_id'), 'security_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_security_events_created_at'), 'security_events', ['created_at'], unique=False)
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index(op.f('ix_security_events_created_at'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_user_id'), table_name='security_events')
    op.drop_index(op.f('ix_security_events_event_type'), table_name='security_events')
    op.drop_table('security_events')
    
    op.drop_index(op.f('ix_failed_login_attempts_last_attempt'), table_name='failed_login_attempts')
    op.drop_index(op.f('ix_failed_login_attempts_user_email'), table_name='failed_login_attempts')
    op.drop_table('failed_login_attempts')