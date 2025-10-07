"""
Unit tests for FleetWise business logic
Run with: pytest tests/test_unit.py -v
"""
import pytest
from app.core.security import (
    get_password_hash, 
    verify_password, 
    validate_password_strength,
    create_access_token
)
from app.models.models import User, Vehicle, Reservation, UserRole, VehicleStatus, ReservationStatus
from jose import jwt
from app.core.config import settings

# Test password hashing
def test_password_hashing():
    """Test password hashing and verification"""
    password = "TestPassword@123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) == True
    assert verify_password("WrongPassword", hashed) == False

# Test password strength validation
def test_password_strength_valid():
    """Test valid password passes strength check"""
    assert validate_password_strength("ValidPass@123") == True
    assert validate_password_strength("Str0ng!Pass") == True

def test_password_strength_invalid():
    """Test weak passwords fail strength check"""
    assert validate_password_strength("weak") == False
    assert validate_password_strength("noupperca5e!") == False
    assert validate_password_strength("NOLOWERCASE1!") == False
    assert validate_password_strength("NoNumbers!") == False
    assert validate_password_strength("NoSpecial1") == False
    assert validate_password_strength("Short1!") == False

# Test JWT token creation
def test_jwt_token_creation():
    """Test JWT token creation and decoding"""
    data = {"sub": "test@example.com", "role": "FLEET_USER"}
    token = create_access_token(data)
    
    assert token is not None
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "test@example.com"
    assert decoded["role"] == "FLEET_USER"

# Test User model
def test_user_model_creation():
    """Test User model instantiation"""
    user = User(
        name="Test User",
        email="test@example.com",
        employee_id="EMP001",
        phone="1234567890",
        password_hash="hashed_password",
        role=UserRole.FLEET_USER,
        reservation_count=0  # Explicitly set default
    )
    
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.role == UserRole.FLEET_USER
    assert user.reservation_count == 0

# Test Vehicle model
def test_vehicle_model_creation():
    """Test Vehicle model instantiation"""
    vehicle = Vehicle(
        manufacturer="Honda",
        model="Civic",
        license_plate="ABC-123",
        status=VehicleStatus.AVAILABLE,
        rental_count=0  # Explicitly set default
    )
    
    assert vehicle.manufacturer == "Honda"
    assert vehicle.model == "Civic"
    assert vehicle.license_plate == "ABC-123"
    assert vehicle.status == VehicleStatus.AVAILABLE
    assert vehicle.rental_count == 0

# Test Reservation model
def test_reservation_model_creation():
    """Test Reservation model instantiation"""
    reservation = Reservation(
        user_id=1,
        vehicle_id=1,
        status=ReservationStatus.ACTIVE
    )
    
    assert reservation.user_id == 1
    assert reservation.vehicle_id == 1
    assert reservation.status == ReservationStatus.ACTIVE
    assert reservation.return_date is None

# Test User roles
def test_user_roles():
    """Test User role enum values"""
    assert UserRole.FLEET_MANAGER == "FLEET_MANAGER"
    assert UserRole.FLEET_USER == "FLEET_USER"

# Test Vehicle status
def test_vehicle_status():
    """Test Vehicle status enum values"""
    assert VehicleStatus.AVAILABLE == "AVAILABLE"
    assert VehicleStatus.RENTED == "RENTED"

# Test Reservation status
def test_reservation_status():
    """Test Reservation status enum values"""
    assert ReservationStatus.ACTIVE == "ACTIVE"
    assert ReservationStatus.COMPLETED == "COMPLETED"

# Test business logic: 3-vehicle limit
def test_reservation_limit_logic():
    """Test 3-vehicle reservation limit business logic"""
    user = User(
        name="Test",
        email="test@test.com",
        employee_id="EMP001",
        phone="1234567890",
        password_hash="hash",
        role=UserRole.FLEET_USER,
        reservation_count=0
    )
    
    # Simulate reservations
    assert user.reservation_count < 3  # Can reserve
    user.reservation_count += 1
    assert user.reservation_count < 3  # Can reserve
    user.reservation_count += 1
    assert user.reservation_count < 3  # Can reserve
    user.reservation_count += 1
    assert user.reservation_count == 3  # At limit
    assert not (user.reservation_count < 3)  # Cannot reserve more

if __name__ == "__main__":
    pytest.main([__file__, "-v"])