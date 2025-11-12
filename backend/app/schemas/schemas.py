from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.models import UserRole, VehicleStatus, ReservationStatus

# User Schemas
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    employee_id: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)  # Changed: Optional and no min_length

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    user_id: int
    role: UserRole
    reservation_count: int
    email_verified: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)  # Changed: No min_length

# Vehicle Schemas
class VehicleBase(BaseModel):
    manufacturer: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    license_plate: str = Field(..., min_length=1, max_length=20)

class VehicleCreate(VehicleBase):
    pass

class VehicleResponse(VehicleBase):
    vehicle_id: int
    status: VehicleStatus
    rental_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class VehicleUpdate(BaseModel):
    manufacturer: Optional[str] = Field(None, min_length=1, max_length=50)
    model: Optional[str] = Field(None, min_length=1, max_length=50)
    license_plate: Optional[str] = Field(None, min_length=1, max_length=20)

# Reservation Schemas
class ReservationCreate(BaseModel):
    user_id: int
    vehicle_id: int

class ReservationReturn(BaseModel):
    reservation_id: int

class ReservationResponse(BaseModel):
    reservation_id: int
    user_id: int
    vehicle_id: int
    reservation_date: datetime
    return_date: Optional[datetime]
    status: ReservationStatus
    
    model_config = ConfigDict(from_attributes=True)

class ReservationWithDetails(ReservationResponse):
    user: UserResponse
    vehicle: VehicleResponse
    
    model_config = ConfigDict(from_attributes=True)

# Chatbot Schemas
class ManufacturerResponse(BaseModel):
    manufacturers: list[str]

class ModelResponse(BaseModel):
    models: list[str]

class AvailabilityQuery(BaseModel):
    manufacturer: str
    model: str

class AvailabilityResponse(BaseModel):
    manufacturer: str
    model: str
    available: bool
    total_count: int
    available_count: int
    message: str

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None