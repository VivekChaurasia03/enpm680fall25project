from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List

from app.core.database import get_db
from app.core.security import get_current_fleet_user
from app.models.models import Vehicle, VehicleStatus, User
from app.schemas.schemas import (
    ManufacturerResponse, 
    ModelResponse, 
    AvailabilityQuery,
    AvailabilityResponse
)

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

@router.get("/manufacturers", response_model=ManufacturerResponse)
async def get_manufacturers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_user)
):
    """
    Get list of available manufacturers for chatbot selection.
    FR-002: Check Vehicle Availability via Chatbot (Step 1)
    Fleet User only.
    """
    result = await db.execute(
        select(Vehicle.manufacturer).distinct().order_by(Vehicle.manufacturer)
    )
    manufacturers = [row[0] for row in result.all()]
    
    return ManufacturerResponse(manufacturers=manufacturers)

@router.get("/models", response_model=ModelResponse)
async def get_models(
    manufacturer: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_user)
):
    """
    Get list of models for a specific manufacturer.
    FR-002: Check Vehicle Availability via Chatbot (Step 2)
    Fleet User only.
    """
    result = await db.execute(
        select(Vehicle.model)
        .where(Vehicle.manufacturer == manufacturer)
        .distinct()
        .order_by(Vehicle.model)
    )
    models = [row[0] for row in result.all()]
    
    if not models:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No vehicles found for manufacturer: {manufacturer}"
        )
    
    return ModelResponse(models=models)

@router.post("/availability", response_model=AvailabilityResponse)
async def check_availability(
    query: AvailabilityQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_user)
):
    """
    Check availability of a specific vehicle type (manufacturer + model).
    FR-002: Check Vehicle Availability via Chatbot (Step 3)
    Fleet User only.
    """
    # Get total count of matching vehicles
    total_result = await db.execute(
        select(func.count(Vehicle.vehicle_id))
        .where(
            and_(
                Vehicle.manufacturer == query.manufacturer,
                Vehicle.model == query.model
            )
        )
    )
    total_count = total_result.scalar()
    
    if total_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {query.manufacturer} {query.model} vehicles in the fleet"
        )
    
    # Get available count
    available_result = await db.execute(
        select(func.count(Vehicle.vehicle_id))
        .where(
            and_(
                Vehicle.manufacturer == query.manufacturer,
                Vehicle.model == query.model,
                Vehicle.status == VehicleStatus.AVAILABLE
            )
        )
    )
    available_count = available_result.scalar()
    
    # Build response message
    if available_count > 0:
        message = f"Good news! There are {available_count} {query.manufacturer} {query.model} vehicle(s) available for reservation."
        available = True
    else:
        message = f"Sorry, all {total_count} {query.manufacturer} {query.model} vehicle(s) are currently rented. Please check back later or try a different model."
        available = False
    
    return AvailabilityResponse(
        manufacturer=query.manufacturer,
        model=query.model,
        available=available,
        total_count=total_count,
        available_count=available_count,
        message=message
    )