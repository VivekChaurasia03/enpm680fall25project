from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User, UserRole
from app.models.audit_log import FailedLoginAttempt
from app.schemas.schemas import TokenData
from app.core.audit_logger import audit_logger
import re

# Password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        
        if email is None:
            raise credentials_exception
        
        token_data = TokenData(email=email, role=role)
    except JWTError:
        raise credentials_exception
    
    # Query user from database
    result = await db.execute(select(User).where(User.email == token_data.email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    # Verify role matches (additional security check)
    if user.role != token_data.role:
        raise credentials_exception
    
    return user

async def get_current_fleet_manager(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to ensure current user is a Fleet Manager"""
    if current_user.role != UserRole.FLEET_MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires Fleet Manager privileges"
        )
    return current_user

async def get_current_fleet_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to ensure current user is a Fleet User"""
    if current_user.role != UserRole.FLEET_USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation is only available to Fleet Users"
        )
    return current_user

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements based on configuration.
    Returns: (is_valid, error_message)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
    
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, "Password must contain at least one special character"
    
    return True, ""


async def check_account_lockout(email: str, db: AsyncSession) -> Tuple[bool, Optional[int]]:
    """
    Check if account is locked due to failed login attempts.
    Returns: (is_locked, remaining_minutes)
    """
    # Get failed login attempts for this email
    result = await db.execute(
        select(FailedLoginAttempt).where(FailedLoginAttempt.user_email == email)
    )
    failed_attempt = result.scalar_one_or_none()
    
    if not failed_attempt:
        return False, None
    
    # Check if account is currently locked
    if failed_attempt.is_locked:
        return True, failed_attempt.lockout_remaining_minutes
    
    return False, None


async def handle_failed_login(email: str, ip_address: str, db: AsyncSession) -> None:
    """Handle a failed login attempt, implementing account lockout policy."""
    
    # Get existing failed attempts record
    result = await db.execute(
        select(FailedLoginAttempt).where(FailedLoginAttempt.user_email == email)
    )
    failed_attempt = result.scalar_one_or_none()
    
    if failed_attempt:
        # Update existing record
        failed_attempt.attempt_count += 1
        failed_attempt.last_attempt = datetime.utcnow()
        failed_attempt.ip_address = ip_address
        
        # Check if we should lock the account
        if failed_attempt.attempt_count >= settings.MAX_LOGIN_ATTEMPTS:
            failed_attempt.locked_until = datetime.utcnow() + timedelta(
                minutes=settings.LOCKOUT_DURATION_MINUTES
            )
            
            # Log account lockout
            audit_logger.log_security_event(
                event_type="ACCOUNT_LOCKED",
                severity="WARNING",
                ip_address=ip_address,
                details={
                    "user_email": email,
                    "attempt_count": failed_attempt.attempt_count,
                    "lockout_duration_minutes": settings.LOCKOUT_DURATION_MINUTES
                }
            )
    else:
        # Create new failed attempts record
        failed_attempt = FailedLoginAttempt(
            user_email=email,
            attempt_count=1,
            ip_address=ip_address
        )
        db.add(failed_attempt)
    
    await db.commit()


async def handle_successful_login(email: str, db: AsyncSession) -> None:
    """Handle a successful login by clearing failed attempts."""
    
    # Remove failed login attempts record for this user
    await db.execute(
        delete(FailedLoginAttempt).where(FailedLoginAttempt.user_email == email)
    )
    await db.commit()


async def authenticate_user(email: str, password: str, request: Request, db: AsyncSession) -> Optional[User]:
    """
    Authenticate user with enhanced security logging and account lockout.
    """
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    # Check if account is locked
    is_locked, remaining_minutes = await check_account_lockout(email, db)
    if is_locked:
        audit_logger.log_authentication_attempt(
            user_email=email,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=f"Account locked for {remaining_minutes} minutes"
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is locked. Try again in {remaining_minutes} minutes."
        )
    
    # Query user from database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(password, user.password_hash):
        # Handle failed login
        await handle_failed_login(email, ip_address, db)
        
        # Log failed authentication
        audit_logger.log_authentication_attempt(
            user_email=email,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason="Invalid credentials"
        )
        return None
    
    # Handle successful login
    await handle_successful_login(email, db)
    
    # Log successful authentication
    audit_logger.log_authentication_attempt(
        user_email=email,
        success=True,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return user