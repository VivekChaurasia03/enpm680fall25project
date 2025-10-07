from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, get_current_fleet_manager
from app.models.models import (
    Reservation, Vehicle, User, 
    ReservationStatus, VehicleStatus, UserRole
)
from app.schemas.schemas import (
    ReservationCreate, ReservationResponse, 
    ReservationWithDetails
)

router = APIRouter(prefix="/api/reservations", tags=["reservations"])

@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    reservation_data: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_manager)
):
    """
    Process a new vehicle reservation (Fleet Manager only).
    FR-003: Process Vehicle Reservation
    """
    # Get user
    result = await db.execute(select(User).where(User.user_id == reservation_data.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user is Fleet User (Fleet Managers cannot reserve vehicles)
    if user.role != UserRole.FLEET_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Fleet Users can make reservations"
        )
    
    # Check 3-vehicle limit
    if user.reservation_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has reached maximum reservation limit (3 vehicles)"
        )
    
    # Get vehicle
    result = await db.execute(select(Vehicle).where(Vehicle.vehicle_id == reservation_data.vehicle_id))
    vehicle = result.scalar_one_or_none()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    # Check vehicle availability
    if vehicle.status != VehicleStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle is not available for reservation"
        )
    
    # Create reservation
    new_reservation = Reservation(
        user_id=reservation_data.user_id,
        vehicle_id=reservation_data.vehicle_id,
        status=ReservationStatus.ACTIVE
    )
    
    # Update vehicle status
    vehicle.status = VehicleStatus.RENTED
    vehicle.rental_count += 1
    
    # Update user reservation count
    user.reservation_count += 1
    
    db.add(new_reservation)
    await db.commit()
    await db.refresh(new_reservation)
    
    return new_reservation

@router.post("/return", response_model=ReservationResponse)
async def return_vehicle(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_manager)
):
    """
    Process vehicle return (Fleet Manager only).
    FR-004: Return Reserved Vehicle
    """
    # Get reservation with relationships
    result = await db.execute(
        select(Reservation)
        .options(selectinload(Reservation.vehicle), selectinload(Reservation.user))
        .where(Reservation.reservation_id == reservation_id)
    )
    reservation = result.scalar_one_or_none()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    # Check if already returned
    if reservation.status == ReservationStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle has already been returned"
        )
    
    # Update reservation
    reservation.status = ReservationStatus.COMPLETED
    reservation.return_date = datetime.utcnow()
    
    # Update vehicle status
    reservation.vehicle.status = VehicleStatus.AVAILABLE
    
    # Update user reservation count
    reservation.user.reservation_count -= 1
    
    await db.commit()
    await db.refresh(reservation)
    
    return reservation

@router.get("/user/{user_id}", response_model=List[ReservationWithDetails])
async def get_user_reservations(
    user_id: int,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get reservations for a specific user.
    Fleet Users can only see their own reservations.
    Fleet Managers can see any user's reservations.
    """
    # Authorization check
    if current_user.role == UserRole.FLEET_USER and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own reservations"
        )
    
    # Build query
    query = select(Reservation).options(
        selectinload(Reservation.user),
        selectinload(Reservation.vehicle)
    ).where(Reservation.user_id == user_id)
    
    if active_only:
        query = query.where(Reservation.status == ReservationStatus.ACTIVE)
    
    result = await db.execute(query)
    reservations = result.scalars().all()
    
    return reservations

@router.get("", response_model=List[ReservationWithDetails])
async def get_all_reservations(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_manager)
):
    """
    Get all reservations (Fleet Manager only).
    """
    query = select(Reservation).options(
        selectinload(Reservation.user),
        selectinload(Reservation.vehicle)
    )
    
    if active_only:
        query = query.where(Reservation.status == ReservationStatus.ACTIVE)
    
    result = await db.execute(query)
    reservations = result.scalars().all()
    
    return reservations

@router.get("/{reservation_id}", response_model=ReservationWithDetails)
async def get_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific reservation.
    """
    result = await db.execute(
        select(Reservation)
        .options(selectinload(Reservation.user), selectinload(Reservation.vehicle))
        .where(Reservation.reservation_id == reservation_id)
    )
    reservation = result.scalar_one_or_none()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    # Authorization check
    if current_user.role == UserRole.FLEET_USER and current_user.user_id != reservation.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own reservations"
        )
    
    return reservation