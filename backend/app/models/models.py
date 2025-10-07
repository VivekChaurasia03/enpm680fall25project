from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    FLEET_MANAGER = "FLEET_MANAGER"
    FLEET_USER = "FLEET_USER"

class VehicleStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    RENTED = "RENTED"

class ReservationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.FLEET_USER)
    reservation_count = Column(Integer, nullable=False, default=0)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    reservations = relationship("Reservation", back_populates="user", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('reservation_count >= 0 AND reservation_count <= 3', name='check_reservation_limit'),
    )

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    vehicle_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    manufacturer = Column(String(50), nullable=False, index=True)
    model = Column(String(50), nullable=False, index=True)
    license_plate = Column(String(20), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(VehicleStatus), nullable=False, default=VehicleStatus.AVAILABLE)
    rental_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    reservations = relationship("Reservation", back_populates="vehicle", cascade="all, delete-orphan")

class Reservation(Base):
    __tablename__ = "reservations"
    
    reservation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), nullable=False, index=True)
    reservation_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    return_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(ReservationStatus), nullable=False, default=ReservationStatus.ACTIVE)
    
    # Relationships
    user = relationship("User", back_populates="reservations")
    vehicle = relationship("Vehicle", back_populates="reservations")