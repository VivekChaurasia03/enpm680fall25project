from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    validate_password_strength,
    get_current_user,
    authenticate_user,
    check_account_lockout,
    handle_failed_login,
    handle_successful_login
)
from app.core.config import settings
from app.core.audit_logger import audit_logger
from app.models.models import User, UserRole
from app.schemas.schemas import UserCreate, UserResponse, Token
from app.validators.user_validator import UserRegistrationInput, validate_user_id

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register_user(
    user_data: UserRegistrationInput,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new Fleet User account with enhanced security validation.
    Fleet Managers cannot be created through this endpoint (pre-seeded in database).
    """
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    # Enhanced password validation
    is_valid, error_message = validate_password_strength(user_data.password)
    if not is_valid:
        audit_logger.log_input_validation_failure(
            validation_type="WEAK_PASSWORD_REGISTRATION",
            input_value="[password redacted]",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        audit_logger.log_input_validation_failure(
            validation_type="DUPLICATE_EMAIL_REGISTRATION",
            input_value=user_data.email,
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if employee_id already exists
    result = await db.execute(select(User).where(User.employee_id == user_data.employee_id))
    if result.scalar_one_or_none():
        audit_logger.log_input_validation_failure(
            validation_type="DUPLICATE_EMPLOYEE_ID_REGISTRATION",
            input_value=user_data.employee_id,
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already registered"
        )
    
    try:
        # Create new user (always FLEET_USER role for registration)
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            employee_id=user_data.employee_id,
            phone=user_data.phone,
            password_hash=get_password_hash(user_data.password),
            role=UserRole.FLEET_USER,
            reservation_count=0,
            email_verified=False
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # Log successful registration
        audit_logger.log_user_action(
            user_id=new_user.user_id,
            action="USER_REGISTRATION",
            resource_type="USER",
            resource_id=new_user.user_id,
            result="SUCCESS",
            ip_address=ip_address,
            details={
                "email": user_data.email,
                "employee_id": user_data.employee_id,
                "role": "FLEET_USER",
                "user_agent": user_agent
            }
        )
        
        return new_user
        
    except Exception as e:
        await db.rollback()
        audit_logger.log_system_error(
            error_type="USER_REGISTRATION_ERROR",
            error_message=str(e),
            endpoint="/api/auth/register",
            details={
                "email": user_data.email,
                "ip_address": ip_address
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/login")
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with enhanced security including account lockout protection.
    Works for both Fleet Managers and Fleet Users.
    """
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    email = form_data.username
    
    try:
        # Use enhanced authentication with account lockout protection
        user = await authenticate_user(email, form_data.password, request, db)
        
        if not user:
            # Authentication failed - authenticate_user handles logging
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token with user email and role
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role.value, "type": "access"},
            expires_delta=access_token_expires
        )
        
        # Log successful login action
        audit_logger.log_user_action(
            user_id=user.user_id,
            action="LOGIN_SUCCESS",
            resource_type="AUTH",
            result="SUCCESS",
            ip_address=ip_address,
            details={
                "email": user.email,
                "role": user.role.value,
                "user_agent": user_agent
            }
        )
        
        # Return token AND user data (excluding sensitive fields)
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "employee_id": user.employee_id,
                "phone": user.phone,
                "role": user.role.value,
                "reservation_count": user.reservation_count,
                "email_verified": user.email_verified,
                "created_at": user.created_at.isoformat()
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like account lockout)
        raise
    except Exception as e:
        # Log unexpected errors
        audit_logger.log_system_error(
            error_type="LOGIN_SYSTEM_ERROR",
            error_message=str(e),
            endpoint="/api/auth/login",
            details={
                "email": email,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile information with audit logging.
    """
    ip_address = request.client.host if request.client else "unknown"
    
    # Log profile access
    audit_logger.log_user_action(
        user_id=current_user.user_id,
        action="VIEW_PROFILE",
        resource_type="USER",
        resource_id=current_user.user_id,
        result="SUCCESS",
        ip_address=ip_address
    )
    
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (client-side token invalidation).
    In a production system, this would also blacklist the token.
    """
    ip_address = request.client.host if request.client else "unknown"
    
    # Log logout action
    audit_logger.log_user_action(
        user_id=current_user.user_id,
        action="LOGOUT",
        resource_type="AUTH",
        result="SUCCESS",
        ip_address=ip_address,
        details={
            "email": current_user.email,
            "role": current_user.role.value
        }
    )
    
    return {"message": "Logged out successfully"}


@router.get("/check-lockout/{email}")
@limiter.limit("10/minute")
async def check_account_lockout_status(
    request: Request,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if an account is locked (for frontend UX).
    Rate limited to prevent abuse.
    """
    ip_address = request.client.host if request.client else "unknown"
    
    # Validate email format (basic validation)
    if "@" not in email or len(email) > 254:
        audit_logger.log_input_validation_failure(
            validation_type="INVALID_EMAIL_LOCKOUT_CHECK",
            input_value=email[:100],
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    try:
        is_locked, remaining_minutes = await check_account_lockout(email, db)
        
        # Log the check (for security monitoring)
        audit_logger.log_app_event(
            event_type="LOCKOUT_STATUS_CHECK",
            message="Account lockout status checked",
            details={
                "email": email,
                "is_locked": is_locked,
                "ip_address": ip_address
            }
        )
        
        return {
            "is_locked": is_locked,
            "remaining_minutes": remaining_minutes,
            "message": f"Account is locked for {remaining_minutes} more minutes" if is_locked else "Account is not locked"
        }
        
    except Exception as e:
        audit_logger.log_system_error(
            error_type="LOCKOUT_CHECK_ERROR",
            error_message=str(e),
            endpoint="/api/auth/check-lockout",
            details={"email": email, "ip_address": ip_address}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to check account status"
        )