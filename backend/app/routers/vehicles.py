from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.security import get_current_user, get_current_fleet_manager
from app.core.permissions import require_role, require_permission
from app.core.audit_logger import audit_logger
from app.core.config import settings
from app.models.models import Vehicle, Reservation, User, VehicleStatus, ReservationStatus
from app.schemas.schemas import VehicleCreate, VehicleResponse, VehicleUpdate
from app.validators.vehicle_validator import (
    VehicleCreateInput,
    VehicleUpdateInput,
    VehicleSearchInput,
    validate_vehicle_id,
    sanitize_vehicle_data_export
)

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

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
@limiter.limit(settings.RATE_LIMIT_API)
async def get_vehicles(
    request: Request,
    search_params: VehicleSearchInput = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of vehicles with enhanced filtering and security validation.
    Available to all authenticated users.
    """
    ip_address = request.client.host if request.client else "unknown"
    
    try:
        query = select(Vehicle)
        
        # Apply filters if provided (using sanitized search params)
        if search_params.manufacturer:
            query = query.where(Vehicle.manufacturer == search_params.manufacturer)
        if search_params.model:
            query = query.where(Vehicle.model == search_params.model)
        if search_params.status:
            query = query.where(Vehicle.status == search_params.status)
        
        # Apply pagination
        query = query.offset(search_params.offset).limit(search_params.limit)
        
        result = await db.execute(query)
        vehicles = result.scalars().all()
        
        # Log vehicle list access
        audit_logger.log_user_action(
            user_id=current_user.user_id,
            action="VIEW_VEHICLES",
            resource_type="VEHICLE",
            result="SUCCESS",
            ip_address=ip_address,
            details={
                "filters": {
                    "manufacturer": search_params.manufacturer,
                    "model": search_params.model,
                    "status": search_params.status,
                    "limit": search_params.limit,
                    "offset": search_params.offset
                },
                "result_count": len(vehicles)
            }
        )
        
        return vehicles
        
    except Exception as e:
        audit_logger.log_system_error(
            error_type="VEHICLE_LIST_ERROR",
            error_message=str(e),
            user_id=current_user.user_id,
            endpoint="/api/vehicles",
            details={"ip_address": ip_address}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vehicles"
        )

@router.get("/export", response_model=List[dict])
@limiter.limit("5/minute")  # Lower rate limit for export operations
@require_role("FLEET_MANAGER")
async def export_vehicles(
    request: Request,
    search_params: VehicleSearchInput = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export vehicle data in a sanitized format.
    Only Fleet Managers can export vehicle data.
    """
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    try:
        query = select(Vehicle)
        
        # Apply filters
        if search_params.manufacturer:
            query = query.where(Vehicle.manufacturer == search_params.manufacturer)
        if search_params.model:
            query = query.where(Vehicle.model == search_params.model)
        if search_params.status:
            query = query.where(Vehicle.status == search_params.status)
        
        # Apply pagination with a reasonable limit for exports
        export_limit = min(search_params.limit, 1000)  # Max 1000 for export
        query = query.offset(search_params.offset).limit(export_limit)
        
        result = await db.execute(query)
        vehicles = result.scalars().all()
        
        # Sanitize data for export
        sanitized_vehicles = []
        for vehicle in vehicles:
            vehicle_dict = {
                "vehicle_id": vehicle.vehicle_id,
                "manufacturer": vehicle.manufacturer,
                "model": vehicle.model,
                "license_plate": vehicle.license_plate,
                "status": vehicle.status.value,
                "rental_count": vehicle.rental_count,
                "created_at": vehicle.created_at.isoformat()
            }
            sanitized_vehicles.append(sanitize_vehicle_data_export(vehicle_dict))
        
        # Log export action
        audit_logger.log_user_action(
            user_id=current_user.user_id,
            action="EXPORT_VEHICLES",
            resource_type="VEHICLE",
            result="SUCCESS",
            ip_address=ip_address,
            details={
                "export_count": len(sanitized_vehicles),
                "filters": {
                    "manufacturer": search_params.manufacturer,
                    "model": search_params.model,
                    "status": search_params.status
                },
                "user_agent": user_agent
            }
        )
        
        return sanitized_vehicles
        
    except Exception as e:
        audit_logger.log_system_error(
            error_type="VEHICLE_EXPORT_ERROR",
            error_message=str(e),
            user_id=current_user.user_id,
            endpoint="/api/vehicles/export",
            details={"ip_address": ip_address}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export vehicle data"
        )

@router.get("/{vehicle_id}", response_model=VehicleResponse)
@limiter.limit(settings.RATE_LIMIT_API)
async def get_vehicle(
    vehicle_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific vehicle with security validation.
    Available to all authenticated users.
    """
    ip_address = request.client.host if request.client else "unknown"
    
    # Validate vehicle ID
    try:
        validated_vehicle_id = validate_vehicle_id(vehicle_id)
    except ValueError as e:
        audit_logger.log_input_validation_failure(
            validation_type="INVALID_VEHICLE_ID",
            input_value=str(vehicle_id),
            user_id=current_user.user_id,
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    try:
        result = await db.execute(
            select(Vehicle).where(Vehicle.vehicle_id == validated_vehicle_id)
        )
        vehicle = result.scalar_one_or_none()
        
        if not vehicle:
            audit_logger.log_user_action(
                user_id=current_user.user_id,
                action="VIEW_VEHICLE",
                resource_type="VEHICLE",
                resource_id=validated_vehicle_id,
                result="NOT_FOUND",
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        # Log successful vehicle access
        audit_logger.log_user_action(
            user_id=current_user.user_id,
            action="VIEW_VEHICLE",
            resource_type="VEHICLE",
            resource_id=vehicle.vehicle_id,
            result="SUCCESS",
            ip_address=ip_address,
            details={
                "manufacturer": vehicle.manufacturer,
                "model": vehicle.model,
                "license_plate": vehicle.license_plate,
                "status": vehicle.status.value
            }
        )
        
        return vehicle
        
    except HTTPException:
        raise
    except Exception as e:
        audit_logger.log_system_error(
            error_type="VEHICLE_RETRIEVAL_ERROR",
            error_message=str(e),
            user_id=current_user.user_id,
            endpoint=f"/api/vehicles/{vehicle_id}",
            details={"ip_address": ip_address}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vehicle"
        )

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
async def update_vehicle_patch(
    vehicle_id: int,
    vehicle_update: VehicleUpdateInput,
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
    if vehicle_update.license_plate is not None:
        # Check if new license plate already exists
        result = await db.execute(
            select(Vehicle).where(
                and_(
                    Vehicle.license_plate == vehicle_update.license_plate,
                    Vehicle.vehicle_id != vehicle_id
                )
            )
        )
        existing_vehicle = result.scalar_one_or_none()
        
        if existing_vehicle:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vehicle with this license plate already exists"
            )
        
        vehicle.license_plate = vehicle_update.license_plate
    
    await db.commit()
    await db.refresh(vehicle)
    
    return vehicle

# Remove the duplicate PUT endpoint as PATCH is sufficient for partial updates
# This follows RESTful best practices