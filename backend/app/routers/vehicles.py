from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, get_current_fleet_manager
from app.models.models import Vehicle, Reservation, User, VehicleStatus, ReservationStatus
from app.schemas.schemas import VehicleCreate, VehicleResponse, VehicleUpdate

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def add_vehicle(
    vehicle_data: VehicleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_manager)
):
    """
    Add a new vehicle to the fleet (Fleet Manager only).
    FR-001: Add New Vehicle to Fleet
    """
    # Check if license plate already exists
    result = await db.execute(
        select(Vehicle).where(Vehicle.license_plate == vehicle_data.license_plate)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle with this license plate already exists"
        )
    
    # Create new vehicle
    new_vehicle = Vehicle(
        manufacturer=vehicle_data.manufacturer,
        model=vehicle_data.model,
        license_plate=vehicle_data.license_plate,
        status=VehicleStatus.AVAILABLE,
        rental_count=0
    )
    
    db.add(new_vehicle)
    await db.commit()
    await db.refresh(new_vehicle)
    
    return new_vehicle

@router.get("", response_model=List[VehicleResponse])
async def get_vehicles(
    manufacturer: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    status: Optional[VehicleStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of vehicles with optional filtering.
    Available to all authenticated users.
    """
    query = select(Vehicle)
    
    # Apply filters if provided
    if manufacturer:
        query = query.where(Vehicle.manufacturer == manufacturer)
    if model:
        query = query.where(Vehicle.model == model)
    if status:
        query = query.where(Vehicle.status == status)
    
    result = await db.execute(query)
    vehicles = result.scalars().all()
    
    return vehicles

@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific vehicle.
    Available to all authenticated users.
    """
    result = await db.execute(select(Vehicle).where(Vehicle.vehicle_id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    return vehicle

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vehicle(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_manager)
):
    """
    Remove a vehicle from the fleet (Fleet Manager only).
    FR-005: Remove Vehicle from Fleet
    Cannot delete vehicle with active reservations.
    """
    # Find vehicle
    result = await db.execute(select(Vehicle).where(Vehicle.vehicle_id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    # Check for active reservations
    result = await db.execute(
        select(Reservation).where(
            and_(
                Reservation.vehicle_id == vehicle_id,
                Reservation.status == ReservationStatus.ACTIVE
            )
        )
    )
    active_reservation = result.scalar_one_or_none()
    
    if active_reservation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove vehicle with active reservations. Please process the return first."
        )
    
    # Delete vehicle (cascade will handle reservations)
    await db.delete(vehicle)
    await db.commit()
    
    return None

@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: int,
    vehicle_update: VehicleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_manager)
):
    """
    Update vehicle information (Fleet Manager only).
    """
    result = await db.execute(select(Vehicle).where(Vehicle.vehicle_id == vehicle_id))
    vehicle = result.scalar_one_or_none()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    # Update fields if provided
    if vehicle_update.manufacturer is not None:
        vehicle.manufacturer = vehicle_update.manufacturer
    if vehicle_update.model is not None:
        vehicle.model = vehicle_update.model
    
    await db.commit()
    await db.refresh(vehicle)
    
    return vehicle