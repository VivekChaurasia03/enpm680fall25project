from functools import wraps
from typing import List, Optional, Union
from fastapi import HTTPException, status, Depends, Request
from app.models.models import User, UserRole
from app.core.security import get_current_user
from app.core.audit_logger import audit_logger


class Permissions:
    """
    Role-based access control permissions system.
    Defines permissions for different user roles.
    """
    
    # Fleet Manager permissions
    FLEET_MANAGER_PERMISSIONS = {
        "CREATE_VEHICLE",
        "UPDATE_VEHICLE", 
        "DELETE_VEHICLE",
        "VIEW_ALL_VEHICLES",
        "CREATE_RESERVATION",
        "UPDATE_RESERVATION",
        "DELETE_RESERVATION",
        "VIEW_ALL_RESERVATIONS",
        "PROCESS_VEHICLE_RETURN",
        "VIEW_USER_DETAILS",
        "UPDATE_USER_ROLE",
        "VIEW_AUDIT_LOGS",
        "EXPORT_DATA",
        "MANAGE_SYSTEM_CONFIG"
    }
    
    # Fleet User permissions
    FLEET_USER_PERMISSIONS = {
        "VIEW_AVAILABLE_VEHICLES",
        "VIEW_OWN_RESERVATIONS",
        "REQUEST_RESERVATION",
        "CANCEL_OWN_RESERVATION",
        "USE_CHATBOT",
        "VIEW_OWN_PROFILE",
        "UPDATE_OWN_PROFILE"
    }
    
    @classmethod
    def get_user_permissions(cls, role: UserRole) -> set:
        """Get all permissions for a given role"""
        if role == UserRole.FLEET_MANAGER:
            return cls.FLEET_MANAGER_PERMISSIONS | cls.FLEET_USER_PERMISSIONS
        elif role == UserRole.FLEET_USER:
            return cls.FLEET_USER_PERMISSIONS
        else:
            return set()
    
    @classmethod
    def has_permission(cls, user_role: UserRole, permission: str) -> bool:
        """Check if a role has a specific permission"""
        user_permissions = cls.get_user_permissions(user_role)
        return permission in user_permissions


def require_role(allowed_roles: Union[List[str], str]):
    """
    Decorator to enforce role-based access control.
    
    Args:
        allowed_roles: Single role string or list of allowed role strings
        
    Usage:
        @require_role("FLEET_MANAGER")
        @require_role(["FLEET_MANAGER", "FLEET_USER"])
    """
    # Convert single role to list
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            request: Request = None,
            **kwargs
        ):
            # Extract request from kwargs if not passed directly
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if request is None:
                    request = kwargs.get('request')
            
            # Check if user's role is in allowed roles
            if current_user.role.value not in allowed_roles:
                # Get IP address for logging
                ip_address = "unknown"
                if request and hasattr(request, 'client') and request.client:
                    ip_address = request.client.host
                
                # Log unauthorized access attempt
                audit_logger.log_unauthorized_access(
                    user_id=current_user.user_id,
                    user_role=current_user.role.value,
                    required_role=", ".join(allowed_roles),
                    endpoint=func.__name__,
                    ip_address=ip_address
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_permission(required_permission: str):
    """
    Decorator to enforce permission-based access control.
    
    Args:
        required_permission: Permission string required to access the endpoint
        
    Usage:
        @require_permission("CREATE_VEHICLE")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            request: Request = None,
            **kwargs
        ):
            # Extract request from kwargs if not passed directly
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if request is None:
                    request = kwargs.get('request')
            
            # Check if user has required permission
            if not Permissions.has_permission(current_user.role, required_permission):
                # Get IP address for logging
                ip_address = "unknown"
                if request and hasattr(request, 'client') and request.client:
                    ip_address = request.client.host
                
                # Log unauthorized access attempt
                audit_logger.log_unauthorized_access(
                    user_id=current_user.user_id,
                    user_role=current_user.role.value,
                    required_role=f"Permission: {required_permission}",
                    endpoint=func.__name__,
                    ip_address=ip_address
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required permission: {required_permission}"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_any_role(allowed_roles: List[str]):
    """
    Decorator that allows access if user has any of the specified roles.
    Alias for require_role for clarity.
    """
    return require_role(allowed_roles)


def require_all_roles(required_roles: List[str]):
    """
    Decorator that requires user to have ALL specified roles.
    Note: In current system, users have only one role, so this is for future extensibility.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            request: Request = None,
            **kwargs
        ):
            # Extract request
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if request is None:
                    request = kwargs.get('request')
            
            # Check if user has all required roles (currently only supports single role)
            user_role = current_user.role.value
            if user_role not in required_roles:
                # Get IP address for logging
                ip_address = "unknown"
                if request and hasattr(request, 'client') and request.client:
                    ip_address = request.client.host
                
                # Log unauthorized access attempt
                audit_logger.log_unauthorized_access(
                    user_id=current_user.user_id,
                    user_role=user_role,
                    required_role=", ".join(required_roles),
                    endpoint=func.__name__,
                    ip_address=ip_address
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(required_roles)}"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_self_or_admin(user_id_param: str = "user_id"):
    """
    Decorator that allows access if user is accessing their own data or is an admin.
    
    Args:
        user_id_param: Name of the parameter containing the user ID to check
        
    Usage:
        @require_self_or_admin("user_id")
        async def get_user_profile(user_id: int, current_user: User):
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            request: Request = None,
            **kwargs
        ):
            # Extract request
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if request is None:
                    request = kwargs.get('request')
            
            # Get the user ID from parameters
            target_user_id = kwargs.get(user_id_param)
            if target_user_id is None:
                # Try to get from path parameters
                if hasattr(request, 'path_params'):
                    target_user_id = request.path_params.get(user_id_param)
            
            # Allow if user is accessing their own data
            if target_user_id == current_user.user_id:
                return await func(*args, current_user=current_user, **kwargs)
            
            # Allow if user is a Fleet Manager (admin)
            if current_user.role == UserRole.FLEET_MANAGER:
                return await func(*args, current_user=current_user, **kwargs)
            
            # Deny access
            ip_address = "unknown"
            if request and hasattr(request, 'client') and request.client:
                ip_address = request.client.host
            
            audit_logger.log_unauthorized_access(
                user_id=current_user.user_id,
                user_role=current_user.role.value,
                required_role="SELF_OR_ADMIN",
                endpoint=func.__name__,
                ip_address=ip_address
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only access your own data."
            )
        return wrapper
    return decorator


async def check_resource_ownership(
    current_user: User,
    resource_type: str,
    resource_id: int,
    db_session
) -> bool:
    """
    Check if user owns a specific resource (e.g., reservation).
    
    Args:
        current_user: Current authenticated user
        resource_type: Type of resource (reservation, etc.)
        resource_id: ID of the resource
        db_session: Database session
        
    Returns:
        bool: True if user owns the resource or is admin
    """
    from sqlalchemy import select
    
    # Fleet Managers have access to all resources
    if current_user.role == UserRole.FLEET_MANAGER:
        return True
    
    if resource_type == "reservation":
        from app.models.models import Reservation
        result = await db_session.execute(
            select(Reservation).where(
                Reservation.reservation_id == resource_id,
                Reservation.user_id == current_user.user_id
            )
        )
        return result.scalar_one_or_none() is not None
    
    # Add other resource types as needed
    return False


def require_resource_ownership(resource_type: str, resource_id_param: str = "id"):
    """
    Decorator that requires user to own the resource or be an admin.
    
    Args:
        resource_type: Type of resource to check ownership for
        resource_id_param: Name of parameter containing resource ID
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            request: Request = None,
            **kwargs
        ):
            from app.core.database import get_db
            
            # Get database session
            db = None
            for arg in args:
                if hasattr(arg, 'execute'):  # Likely a database session
                    db = arg
                    break
            
            if db is None:
                # Try to get from dependency injection
                db = await anext(get_db())
            
            # Extract request
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if request is None:
                    request = kwargs.get('request')
            
            # Get resource ID
            resource_id = kwargs.get(resource_id_param)
            if resource_id is None and hasattr(request, 'path_params'):
                resource_id = request.path_params.get(resource_id_param)
            
            if resource_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Resource ID not found"
                )
            
            # Check ownership
            has_access = await check_resource_ownership(
                current_user, resource_type, resource_id, db
            )
            
            if not has_access:
                ip_address = "unknown"
                if request and hasattr(request, 'client') and request.client:
                    ip_address = request.client.host
                
                audit_logger.log_unauthorized_access(
                    user_id=current_user.user_id,
                    user_role=current_user.role.value,
                    required_role=f"OWNER_OF_{resource_type.upper()}_{resource_id}",
                    endpoint=func.__name__,
                    ip_address=ip_address
                )
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You don't own this resource."
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


class SecurityContext:
    """
    Context manager for security-related operations.
    Provides utility methods for permission checking.
    """
    
    def __init__(self, user: User, request: Optional[Request] = None):
        self.user = user
        self.request = request
        self.ip_address = "unknown"
        
        if request and hasattr(request, 'client') and request.client:
            self.ip_address = request.client.host
    
    def can(self, permission: str) -> bool:
        """Check if current user has specific permission"""
        return Permissions.has_permission(self.user.role, permission)
    
    def is_role(self, role: str) -> bool:
        """Check if current user has specific role"""
        return self.user.role.value == role
    
    def is_admin(self) -> bool:
        """Check if current user is admin (Fleet Manager)"""
        return self.user.role == UserRole.FLEET_MANAGER
    
    def log_action(self, action: str, resource_type: str, resource_id: Optional[int] = None):
        """Log user action with context"""
        audit_logger.log_user_action(
            user_id=self.user.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=self.ip_address
        )
    
    def log_access_denied(self, endpoint: str, required_permission: str):
        """Log access denied attempt"""
        audit_logger.log_unauthorized_access(
            user_id=self.user.user_id,
            user_role=self.user.role.value,
            required_role=required_permission,
            endpoint=endpoint,
            ip_address=self.ip_address
        )