from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_fleet_manager
from app.models.models import User, UserRole
from app.schemas.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_manager)
):
    """
    Get list of all users (Fleet Manager only).
    """
    try:
        result = await db.execute(select(User).order_by(User.created_at.desc()))
        users = result.scalars().all()
        return list(users)
    except Exception as e:
        print(f"❌ Error in get_all_users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )


@router.get("/fleet-users", response_model=List[UserResponse])
async def get_fleet_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_manager)
):
    """
    Get list of fleet users only (Fleet Manager only).
    """
    try:
        result = await db.execute(
            select(User)
            .where(User.role == UserRole.FLEET_USER)
            .order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        return list(users)
    except Exception as e:
        print(f"❌ Error in get_fleet_users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch fleet users: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_manager)
):
    """
    Get details of a specific user (Fleet Manager only).
    """
    try:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}"
        )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_manager)
):
    """
    Update user information (Fleet Manager only).
    """
    try:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields if provided
        if user_update.name is not None:
            user.name = user_update.name
        if user_update.phone is not None:
            user.phone = user_update.phone
        
        await db.commit()
        await db.refresh(user)
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in update_user: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_fleet_manager)
):
    """
    Delete a user (Fleet Manager only).
    Cannot delete user with active reservations.
    """
    try:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent self-deletion
        if user.user_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Check for active reservations
        if user.reservation_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete user with active reservations. Process returns first."
            )
        
        await db.delete(user)
        await db.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in delete_user: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )