"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-10-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('employee_id', sa.String(length=50), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('FLEET_MANAGER', 'FLEET_USER', name='userrole'), nullable=False),
        sa.Column('reservation_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('reservation_count >= 0 AND reservation_count <= 3', name='check_reservation_limit'),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('employee_id')
    )
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_employee_id'), 'users', ['employee_id'], unique=True)
    
    # Create vehicles table
    op.create_table(
        'vehicles',
        sa.Column('vehicle_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('manufacturer', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('license_plate', sa.String(length=20), nullable=False),
        sa.Column('status', sa.Enum('AVAILABLE', 'RENTED', name='vehiclestatus'), nullable=False, server_default='AVAILABLE'),
        sa.Column('rental_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('vehicle_id'),
        sa.UniqueConstraint('license_plate')
    )
    op.create_index(op.f('ix_vehicles_vehicle_id'), 'vehicles', ['vehicle_id'], unique=False)
    op.create_index(op.f('ix_vehicles_manufacturer'), 'vehicles', ['manufacturer'], unique=False)
    op.create_index(op.f('ix_vehicles_model'), 'vehicles', ['model'], unique=False)
    op.create_index(op.f('ix_vehicles_license_plate'), 'vehicles', ['license_plate'], unique=True)
    
    # Create reservations table
    op.create_table(
        'reservations',
        sa.Column('reservation_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('reservation_date', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('return_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'COMPLETED', name='reservationstatus'), nullable=False, server_default='ACTIVE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.vehicle_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('reservation_id')
    )
    op.create_index(op.f('ix_reservations_reservation_id'), 'reservations', ['reservation_id'], unique=False)
    op.create_index(op.f('ix_reservations_user_id'), 'reservations', ['user_id'], unique=False)
    op.create_index(op.f('ix_reservations_vehicle_id'), 'reservations', ['vehicle_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reservations_vehicle_id'), table_name='reservations')
    op.drop_index(op.f('ix_reservations_user_id'), table_name='reservations')
    op.drop_index(op.f('ix_reservations_reservation_id'), table_name='reservations')
    op.drop_table('reservations')
    
    op.drop_index(op.f('ix_vehicles_license_plate'), table_name='vehicles')
    op.drop_index(op.f('ix_vehicles_model'), table_name='vehicles')
    op.drop_index(op.f('ix_vehicles_manufacturer'), table_name='vehicles')
    op.drop_index(op.f('ix_vehicles_vehicle_id'), table_name='vehicles')
    op.drop_table('vehicles')
    
    op.drop_index(op.f('ix_users_employee_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_user_id'), table_name='users')
    op.drop_table('users')