import time
import json
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.audit_logger import audit_logger
from datetime import datetime


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive request/response logging middleware.
    Logs all HTTP requests and responses with security context.
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics", 
            "/favicon.ico",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        # Define sensitive endpoints that need extra logging
        self.sensitive_endpoints = [
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/vehicles",
            "/reservations",
            "/users"
        ]
        
        # Define endpoints that should not log request body
        self.no_body_log_endpoints = [
            "/auth/login",  # Don't log passwords
            "/auth/register",  # Don't log passwords
            "/auth/change-password"  # Don't log passwords
        ]
    
    def _should_log_request(self, path: str) -> bool:
        """Determine if request should be logged"""
        return not any(exclude in path for exclude in self.exclude_paths)
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint is sensitive and needs extra logging"""
        return any(sensitive in path for sensitive in self.sensitive_endpoints)
    
    def _should_log_body(self, path: str) -> bool:
        """Determine if request body should be logged"""
        return not any(no_log in path for no_log in self.no_body_log_endpoints)
    
    def _extract_user_info(self, request: Request) -> Dict[str, Any]:
        """Extract user information from request"""
        user_info = {
            "user_id": None,
            "user_email": None,
            "user_role": None
        }
        
        # Try to extract user info from JWT token
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                from jose import jwt
                from app.core.config import settings
                
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_info["user_email"] = payload.get("sub")
                user_info["user_role"] = payload.get("role")
                # In practice, you'd look up user_id from database using email
                user_info["user_id"] = hash(user_info["user_email"]) % 1000000 if user_info["user_email"] else None
        except Exception:
            # User is not authenticated or token is invalid
            pass
        
        return user_info
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize headers by removing sensitive information"""
        sanitized = {}
        sensitive_headers = {
            "authorization", "cookie", "x-api-key", "x-auth-token",
            "set-cookie", "proxy-authorization"
        }
        
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            elif key_lower.startswith("x-") and ("key" in key_lower or "token" in key_lower):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def _get_request_body(self, request: Request) -> Optional[str]:
        """Safely get request body for logging"""
        if not self._should_log_body(request.url.path):
            return "[BODY_NOT_LOGGED]"
        
        try:
            # Get body
            body = await request.body()
            if not body:
                return None
            
            # Try to decode as JSON for better formatting
            try:
                body_json = json.loads(body.decode('utf-8'))
                # Remove sensitive fields
                if isinstance(body_json, dict):
                    sensitive_fields = ["password", "token", "secret", "key", "auth"]
                    for field in sensitive_fields:
                        if field in body_json:
                            body_json[field] = "[REDACTED]"
                return json.dumps(body_json, separators=(',', ':'))[:1000]  # Limit size
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Return raw body if not JSON (limit size)
                return body.decode('utf-8', errors='ignore')[:500]
        
        except Exception as e:
            audit_logger.log_system_error(
                error_type="REQUEST_BODY_READ_ERROR",
                error_message=str(e)
            )
            return "[BODY_READ_ERROR]"
    
    def _get_response_size(self, response: Response) -> int:
        """Get response size in bytes"""
        try:
            if hasattr(response, 'body') and response.body:
                return len(response.body)
            elif hasattr(response, 'content') and response.content:
                return len(response.content)
            else:
                return 0
        except Exception:
            return 0
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Main middleware dispatch method"""
        # Skip logging for excluded paths
        if not self._should_log_request(request.url.path):
            return await call_next(request)
        
        # Capture request start time
        start_time = time.time()
        request_timestamp = datetime.utcnow().isoformat()
        
        # Extract request information
        user_info = self._extract_user_info(request)
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Get request body (if applicable)
        request_body = None
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            # Store original body for later use by the application
            body = await request.body()
            # Create a new request with the same body
            from starlette.requests import Request as StarletteRequest
            
            async def receive():
                return {"type": "http.request", "body": body}
            
            request._receive = receive
            
            # Get body for logging
            if body and self._should_log_body(request.url.path):
                try:
                    body_str = body.decode('utf-8')
                    if len(body_str) > 1000:
                        body_str = body_str[:1000] + "...[TRUNCATED]"
                    
                    # Try to parse as JSON and sanitize
                    try:
                        body_json = json.loads(body_str)
                        if isinstance(body_json, dict):
                            # Remove sensitive fields
                            sensitive_fields = ["password", "token", "secret", "key", "auth"]
                            for field in sensitive_fields:
                                if field in body_json:
                                    body_json[field] = "[REDACTED]"
                            request_body = json.dumps(body_json, separators=(',', ':'))
                        else:
                            request_body = body_str
                    except json.JSONDecodeError:
                        request_body = body_str
                except UnicodeDecodeError:
                    request_body = "[BINARY_DATA]"
            else:
                request_body = "[NOT_LOGGED]" if body else None
        
        # Log request start
        request_log = {
            "timestamp": request_timestamp,
            "type": "REQUEST_START",
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params) if request.query_params else None,
            "headers": self._sanitize_headers(dict(request.headers)),
            "body": request_body,
            "ip_address": ip_address,
            "user_agent": user_agent,
            **user_info
        }
        
        # Log sensitive endpoint access
        if self._is_sensitive_endpoint(request.url.path):
            audit_logger.log_user_action(
                user_id=user_info.get("user_id"),
                action=f"ACCESS_{request.method}",
                resource_type="ENDPOINT",
                resource_id=None,
                result="STARTED",
                ip_address=ip_address,
                details={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "user_agent": user_agent
                }
            )
        
        # Process request
        error_occurred = False
        response_status = None
        error_details = None
        
        try:
            response = await call_next(request)
            response_status = response.status_code
            
        except Exception as e:
            error_occurred = True
            error_details = str(e)
            response_status = 500
            
            # Log error
            audit_logger.log_system_error(
                error_type="REQUEST_PROCESSING_ERROR",
                error_message=str(e),
                user_id=user_info.get("user_id"),
                endpoint=request.url.path,
                details={
                    "method": request.method,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
            )
            
            # Create error response
            from fastapi.responses import JSONResponse
            response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Get response information
        response_size = self._get_response_size(response)
        
        # Log response
        response_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "REQUEST_COMPLETE",
            "method": request.method,
            "path": request.url.path,
            "status_code": response_status,
            "response_size": response_size,
            "process_time": round(process_time * 1000, 2),  # milliseconds
            "ip_address": ip_address,
            "error": error_occurred,
            "error_details": error_details,
            **user_info
        }
        
        # Log to appropriate logger based on status code
        if response_status >= 500:
            audit_logger.log_system_error(
                error_type="HTTP_SERVER_ERROR",
                error_message=f"HTTP {response_status} error",
                endpoint=request.url.path,
                details=response_log
            )
        elif response_status >= 400:
            if response_status == 401:
                audit_logger.log_security_event(
                    event_type="UNAUTHORIZED_ACCESS",
                    severity="WARNING",
                    user_id=user_info.get("user_id"),
                    ip_address=ip_address,
                    details=response_log
                )
            elif response_status == 403:
                audit_logger.log_security_event(
                    event_type="FORBIDDEN_ACCESS",
                    severity="WARNING",
                    user_id=user_info.get("user_id"),
                    ip_address=ip_address,
                    details=response_log
                )
            else:
                audit_logger.log_app_event(
                    event_type="HTTP_CLIENT_ERROR",
                    message=f"HTTP {response_status} client error",
                    details=response_log
                )
        else:
            # Successful request
            audit_logger.log_app_event(
                event_type="HTTP_REQUEST",
                message=f"{request.method} {request.url.path} - {response_status}",
                details=response_log
            )
        
        # Log sensitive endpoint completion
        if self._is_sensitive_endpoint(request.url.path):
            audit_logger.log_user_action(
                user_id=user_info.get("user_id"),
                action=f"ACCESS_{request.method}",
                resource_type="ENDPOINT",
                resource_id=None,
                result="SUCCESS" if response_status < 400 else "FAILURE",
                ip_address=ip_address,
                details={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status_code": response_status,
                    "process_time": process_time
                }
            )
        
        # Add custom headers to response
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        response.headers["X-Request-ID"] = f"{int(start_time * 1000000)}"
        
        return response


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Security-focused logging middleware that specifically monitors for suspicious activity.
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Patterns that indicate potential attacks
        self.suspicious_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"union\s+select",
            r"drop\s+table",
            r"insert\s+into",
            r"delete\s+from",
            r"exec\s*\(",
            r"\.\.\/",
            r"\/etc\/passwd",
            r"cmd\.exe",
            r"powershell",
        ]
    
    def _check_for_suspicious_patterns(self, text: str) -> list:
        """Check text for suspicious patterns"""
        import re
        found_patterns = []
        
        if not text:
            return found_patterns
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found_patterns.append(pattern)
        
        return found_patterns
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Monitor requests for security issues"""
        
        # Extract request information
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        path = request.url.path
        
        # Check URL path for suspicious patterns
        suspicious_in_path = self._check_for_suspicious_patterns(path)
        if suspicious_in_path:
            audit_logger.log_security_event(
                event_type="SUSPICIOUS_URL_PATTERN",
                severity="WARNING",
                ip_address=ip_address,
                details={
                    "path": path,
                    "patterns": suspicious_in_path,
                    "user_agent": user_agent
                }
            )
        
        # Check query parameters
        if request.query_params:
            query_string = str(request.query_params)
            suspicious_in_query = self._check_for_suspicious_patterns(query_string)
            if suspicious_in_query:
                audit_logger.log_security_event(
                    event_type="SUSPICIOUS_QUERY_PATTERN",
                    severity="WARNING",
                    ip_address=ip_address,
                    details={
                        "query_params": query_string[:200],
                        "patterns": suspicious_in_query,
                        "user_agent": user_agent
                    }
                )
        
        # Check request headers for suspicious content
        for header_name, header_value in request.headers.items():
            if header_name.lower() not in ["authorization", "cookie"]:  # Skip auth headers
                suspicious_in_header = self._check_for_suspicious_patterns(header_value)
                if suspicious_in_header:
                    audit_logger.log_security_event(
                        event_type="SUSPICIOUS_HEADER_PATTERN",
                        severity="WARNING",
                        ip_address=ip_address,
                        details={
                            "header_name": header_name,
                            "header_value": header_value[:100],
                            "patterns": suspicious_in_header,
                            "user_agent": user_agent
                        }
                    )
        
        # Check User-Agent for known malicious patterns
        suspicious_user_agents = [
            "sqlmap", "nikto", "nessus", "burp", "nmap", "masscan",
            "dirb", "dirbuster", "gobuster", "wfuzz", "hydra"
        ]
        
        if any(suspicious in user_agent.lower() for suspicious in suspicious_user_agents):
            audit_logger.log_security_event(
                event_type="SUSPICIOUS_USER_AGENT",
                severity="CRITICAL",
                ip_address=ip_address,
                details={
                    "user_agent": user_agent,
                    "path": path
                }
            )
        
        # Process the request
        response = await call_next(request)
        
        return response