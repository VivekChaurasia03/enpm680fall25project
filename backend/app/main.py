from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.audit_logger import audit_logger
from app.routers import auth, vehicles, reservations, chatbot, users
from app.middleware.rate_limiter import rate_limit_middleware
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler, 
    database_exception_handler,
    generic_exception_handler
)
from app.middleware.logging_middleware import RequestLoggingMiddleware, SecurityLoggingMiddleware

app = FastAPI(
    title=settings.APP_NAME,
    description="Fleet Management System for ENPM680 Project - Phase 5 Security Enhanced",
    version="1.0.0"
)

# Add security middleware (order matters!)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityLoggingMiddleware)
app.middleware("http")(rate_limit_middleware)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-Request-ID"],
)

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
app.add_exception_handler(RateLimitExceeded, http_exception_handler)

# Include routers
app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(reservations.router)
app.include_router(chatbot.router)
app.include_router(users.router)

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    audit_logger.log_app_event(
        event_type="APPLICATION_START",
        message="FleetWise API started with Phase 5 security features"
    )

@app.on_event("shutdown") 
async def shutdown_event():
    """Application shutdown event"""
    audit_logger.log_app_event(
        event_type="APPLICATION_SHUTDOWN",
        message="FleetWise API shutting down"
    )

@app.get("/")
async def root():
    return {
        "message": "FleetWise API - Phase 5 Security Enhanced",
        "version": "1.0.0",
        "status": "running",
        "security_features": [
            "JWT Authentication",
            "Role-Based Access Control", 
            "Input Validation",
            "Rate Limiting",
            "Audit Logging",
            "Account Lockout Protection"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2025-11-10T19:30:00Z",
        "security_status": "active"
    }