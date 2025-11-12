import time
from collections import defaultdict, deque
from typing import Dict, Tuple, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.audit_logger import audit_logger
import asyncio
from datetime import datetime, timedelta


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies and comprehensive logging.
    Supports IP-based, user-based, and endpoint-specific rate limiting.
    """
    
    def __init__(self):
        # Storage for rate limiting counters
        self.ip_requests: Dict[str, deque] = defaultdict(deque)
        self.user_requests: Dict[int, deque] = defaultdict(deque)
        self.endpoint_requests: Dict[Tuple[str, str], deque] = defaultdict(deque)
        
        # Lockout tracking
        self.ip_lockouts: Dict[str, datetime] = {}
        self.user_lockouts: Dict[int, datetime] = {}
        
        # Rate limit configurations
        self.rate_limits = {
            "default": {"requests": 100, "window": 60},  # 100 requests per minute
            "auth_login": {"requests": 20, "window": 60},  # 20 login attempts per minute
            "auth_register": {"requests": 10, "window": 60},  # 10 registration attempts per minute
            "chatbot": {"requests": 15, "window": 60},  # 15 chatbot queries per minute
            "vehicle_operations": {"requests": 50, "window": 60},  # 50 vehicle operations per minute
            "reservation_operations": {"requests": 30, "window": 60},  # 30 reservation operations per minute
        }
        
        # Cleanup task
        self.cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up old entries"""
        async def cleanup():
            while True:
                try:
                    await asyncio.sleep(300)  # Run every 5 minutes
                    self._cleanup_old_entries()
                except Exception as e:
                    audit_logger.log_system_error(
                        error_type="RATE_LIMITER_CLEANUP_ERROR",
                        error_message=str(e)
                    )
        
        if self.cleanup_task is None:
            loop = asyncio.get_event_loop()
            self.cleanup_task = loop.create_task(cleanup())
    
    def _cleanup_old_entries(self):
        """Remove old entries from rate limiting storage"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # Remove entries older than 1 hour
        
        # Clean IP requests
        for ip, requests in list(self.ip_requests.items()):
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            if not requests:
                del self.ip_requests[ip]
        
        # Clean user requests
        for user_id, requests in list(self.user_requests.items()):
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            if not requests:
                del self.user_requests[user_id]
        
        # Clean endpoint requests
        for key, requests in list(self.endpoint_requests.items()):
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            if not requests:
                del self.endpoint_requests[key]
        
        # Clean expired lockouts
        current_datetime = datetime.utcnow()
        self.ip_lockouts = {
            ip: lockout_time 
            for ip, lockout_time in self.ip_lockouts.items() 
            if lockout_time > current_datetime
        }
        self.user_lockouts = {
            user_id: lockout_time 
            for user_id, lockout_time in self.user_lockouts.items() 
            if lockout_time > current_datetime
        }
    
    def _get_rate_limit_config(self, endpoint: str, method: str) -> dict:
        """Get rate limit configuration for specific endpoint"""
        endpoint_key = f"{method}_{endpoint}".lower()
        
        # Check for specific endpoint configurations
        if "login" in endpoint_key:
            return self.rate_limits["auth_login"]
        elif "register" in endpoint_key:
            return self.rate_limits["auth_register"]
        elif "chatbot" in endpoint_key:
            return self.rate_limits["chatbot"]
        elif "vehicle" in endpoint_key:
            return self.rate_limits["vehicle_operations"]
        elif "reservation" in endpoint_key:
            return self.rate_limits["reservation_operations"]
        else:
            return self.rate_limits["default"]
    
    def _is_rate_limited(
        self, 
        requests: deque, 
        limit: int, 
        window: int, 
        current_time: float
    ) -> Tuple[bool, int]:
        """
        Check if rate limit is exceeded.
        
        Returns:
            Tuple[bool, int]: (is_limited, remaining_requests)
        """
        # Remove old requests outside the window
        cutoff_time = current_time - window
        while requests and requests[0] < cutoff_time:
            requests.popleft()
        
        # Check if limit is exceeded
        if len(requests) >= limit:
            return True, 0
        else:
            return False, limit - len(requests)
    
    async def check_rate_limit(self, request: Request) -> Optional[Response]:
        """
        Check rate limits for the incoming request.
        
        Returns:
            Optional[Response]: Rate limit response if exceeded, None if allowed
        """
        current_time = time.time()
        ip_address = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        method = request.method
        
        # Get rate limit configuration
        config = self._get_rate_limit_config(endpoint, method)
        limit = config["requests"]
        window = config["window"]
        
        # Check IP lockout
        if ip_address in self.ip_lockouts:
            lockout_time = self.ip_lockouts[ip_address]
            if datetime.utcnow() < lockout_time:
                remaining_seconds = int((lockout_time - datetime.utcnow()).total_seconds())
                audit_logger.log_rate_limit_violation(
                    ip_address=ip_address,
                    endpoint=endpoint,
                    rate_limit=f"IP_LOCKOUT_{remaining_seconds}s"
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "IP address temporarily blocked",
                        "retry_after": remaining_seconds,
                        "message": "Too many violations. Please try again later."
                    }
                )
        
        # Get user ID if authenticated
        user_id = None
        try:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Extract user ID from token (simplified - in practice, decode JWT)
                from jose import jwt
                from app.core.config import settings
                
                token = auth_header.split(" ")[1]
                try:
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                    # This would typically get user_id from database, using email as substitute
                    user_email = payload.get("sub")
                    if user_email:
                        # Simplified - in practice, look up user_id from email
                        user_id = hash(user_email) % 1000000  # Simple hash for demo
                except:
                    pass
        except:
            pass
        
        # Check user-specific lockout
        if user_id and user_id in self.user_lockouts:
            lockout_time = self.user_lockouts[user_id]
            if datetime.utcnow() < lockout_time:
                remaining_seconds = int((lockout_time - datetime.utcnow()).total_seconds())
                audit_logger.log_rate_limit_violation(
                    ip_address=ip_address,
                    endpoint=endpoint,
                    user_id=user_id,
                    rate_limit=f"USER_LOCKOUT_{remaining_seconds}s"
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Account temporarily rate limited",
                        "retry_after": remaining_seconds,
                        "message": "Too many requests from your account."
                    }
                )
        
        # Check IP-based rate limit
        ip_requests = self.ip_requests[ip_address]
        ip_limited, ip_remaining = self._is_rate_limited(ip_requests, limit, window, current_time)
        
        if ip_limited:
            # Check for repeated violations (potential attack)
            violation_count = self._count_recent_violations(ip_address, window=300)  # 5 minutes
            if violation_count >= 5:
                # Temporary IP lockout
                self.ip_lockouts[ip_address] = datetime.utcnow() + timedelta(minutes=15)
                audit_logger.log_security_event(
                    event_type="IP_RATE_LIMIT_LOCKOUT",
                    severity="WARNING",
                    ip_address=ip_address,
                    details={
                        "endpoint": endpoint,
                        "violation_count": violation_count,
                        "lockout_duration": 15
                    }
                )
            
            audit_logger.log_rate_limit_violation(
                ip_address=ip_address,
                endpoint=endpoint,
                user_id=user_id,
                rate_limit=f"{limit}/{window}s"
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": window,
                    "limit": limit,
                    "window": window,
                    "message": f"Too many requests. Maximum {limit} requests per {window} seconds allowed."
                },
                headers={"Retry-After": str(window)}
            )
        
        # Check user-based rate limit (if authenticated)
        if user_id:
            user_requests = self.user_requests[user_id]
            user_limited, user_remaining = self._is_rate_limited(
                user_requests, limit * 2, window, current_time  # Users get 2x limit
            )
            
            if user_limited:
                audit_logger.log_rate_limit_violation(
                    ip_address=ip_address,
                    endpoint=endpoint,
                    user_id=user_id,
                    rate_limit=f"USER_{limit * 2}/{window}s"
                )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "User rate limit exceeded",
                        "retry_after": window,
                        "message": f"Too many requests from your account."
                    }
                )
        
        # Check endpoint-specific rate limit
        endpoint_key = (method, endpoint)
        endpoint_requests = self.endpoint_requests[endpoint_key]
        endpoint_limited, endpoint_remaining = self._is_rate_limited(
            endpoint_requests, limit * 5, window, current_time  # Endpoints get 5x limit
        )
        
        if endpoint_limited:
            audit_logger.log_security_event(
                event_type="ENDPOINT_RATE_LIMIT_EXCEEDED",
                severity="WARNING",
                ip_address=ip_address,
                details={
                    "endpoint": endpoint,
                    "method": method,
                    "limit": limit * 5,
                    "window": window
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Service temporarily overloaded",
                    "retry_after": window,
                    "message": "Service is experiencing high load. Please try again later."
                }
            )
        
        # Record the request
        ip_requests.append(current_time)
        if user_id:
            user_requests.append(current_time)
        endpoint_requests.append(current_time)
        
        # Add rate limit headers to response (will be added in middleware)
        return None
    
    def _count_recent_violations(self, ip_address: str, window: int = 300) -> int:
        """Count recent rate limit violations for an IP"""
        # This is a simplified implementation
        # In practice, you'd track violations in a separate data structure
        return len([
            entry for entry in self.ip_requests.get(ip_address, [])
            if time.time() - entry < window
        ]) // 10  # Rough estimate of violations
    
    def add_rate_limit_headers(self, response: Response, request: Request):
        """Add rate limit headers to response"""
        try:
            ip_address = request.client.host if request.client else "unknown"
            endpoint = request.url.path
            method = request.method
            current_time = time.time()
            
            config = self._get_rate_limit_config(endpoint, method)
            limit = config["requests"]
            window = config["window"]
            
            ip_requests = self.ip_requests.get(ip_address, deque())
            _, remaining = self._is_rate_limited(ip_requests, limit, window, current_time)
            
            # Calculate reset time
            if ip_requests:
                oldest_request = ip_requests[0] if ip_requests else current_time
                reset_time = int(oldest_request + window)
            else:
                reset_time = int(current_time + window)
            
            # Add headers
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            response.headers["X-RateLimit-Window"] = str(window)
            
        except Exception as e:
            # Don't let header addition break the response
            audit_logger.log_system_error(
                error_type="RATE_LIMIT_HEADER_ERROR",
                error_message=str(e)
            )


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.
    """
    # Check rate limit before processing request
    rate_limit_response = await rate_limiter.check_rate_limit(request)
    if rate_limit_response:
        return rate_limit_response
    
    # Process request
    try:
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        rate_limiter.add_rate_limit_headers(response, request)
        
        return response
        
    except Exception as e:
        # Log error and still add headers if possible
        audit_logger.log_system_error(
            error_type="REQUEST_PROCESSING_ERROR",
            error_message=str(e),
            endpoint=request.url.path
        )
        raise