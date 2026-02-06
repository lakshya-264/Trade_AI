"""
Standardized API Response Format and Security Middleware
"""

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional, Union
import time
import uuid
import logging
from datetime import datetime
import asyncio
from collections import defaultdict
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApiResponse:
    """Standardized API response format"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a standardized success response"""
        return {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id or str(uuid.uuid4())
        }
    
    @staticmethod
    def error(
        error: str,
        error_code: str = "GENERIC_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """Create a standardized error response"""
        error_response = {
            "success": False,
            "error": error,
            "error_code": error_code,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id or str(uuid.uuid4())
        }
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True
    
    def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(self.requests[client_id]))

class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """Validate and sanitize symbol input"""
        if not symbol:
            raise HTTPException(
                status_code=400,
                detail="Symbol is required"
            )
        
        # Remove leading/trailing whitespace and convert to uppercase
        symbol = symbol.strip().upper()
        
        # Basic validation - alphanumeric, spaces, dots, and hyphens
        # Allow spaces for index names like "NIFTY BANK", "NIFTY 50"
        if not symbol.replace('.', '').replace('-', '').replace(' ', '').isalnum():
            raise HTTPException(
                status_code=400,
                detail="Invalid symbol format"
            )
        
        # Length validation
        if len(symbol) > 30:  # Increased limit for index names
            raise HTTPException(
                status_code=400,
                detail="Symbol too long"
            )
        
        return symbol
    
    @staticmethod
    def validate_exchange(exchange: str) -> str:
        """Validate exchange input"""
        if not exchange:
            return "NSE"  # Default
        
        exchange = exchange.strip().upper()
        valid_exchanges = ["NSE", "BSE", "NASDAQ", "NYSE"]
        
        if exchange not in valid_exchanges:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid exchange. Must be one of: {', '.join(valid_exchanges)}"
            )
        
        return exchange
    
    @staticmethod
    def validate_timeframe(timeframe: str) -> str:
        """Validate timeframe input"""
        if not timeframe:
            return "1d"  # Default
        
        timeframe = timeframe.strip().lower()
        valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"]
        
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        return timeframe
    
    @staticmethod
    def validate_limit(limit: int, max_limit: int = 1000) -> int:
        """Validate limit parameter"""
        if limit is None:
            return 100  # Default
        
        if not isinstance(limit, int) or limit < 1:
            raise HTTPException(
                status_code=400,
                detail="Limit must be a positive integer"
            )
        
        if limit > max_limit:
            raise HTTPException(
                status_code=400,
                detail=f"Limit cannot exceed {max_limit}"
            )
        
        return limit

class SecurityMiddleware:
    """Security middleware for API protection"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
        self.blocked_ips = set()
        self.suspicious_ips = defaultdict(int)
    
    def get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get real IP from headers (for reverse proxy)
        client_ip = request.headers.get("X-Forwarded-For")
        if not client_ip:
            client_ip = request.headers.get("X-Real-IP")
        if not client_ip:
            client_ip = request.client.host
        
        # Create hash for privacy
        return hashlib.md5(client_ip.encode()).hexdigest()[:16]
    
    async def check_rate_limit(self, request: Request) -> bool:
        """Check if request is within rate limits"""
        client_id = self.get_client_id(request)
        
        if client_id in self.blocked_ips:
            return False
        
        if not self.rate_limiter.is_allowed(client_id):
            # Mark as suspicious
            self.suspicious_ips[client_id] += 1
            
            # Block if too many violations
            if self.suspicious_ips[client_id] > 5:
                self.blocked_ips.add(client_id)
                logger.warning(f"Blocked IP {client_id} for excessive rate limit violations")
            
            return False
        
        return True
    
    async def log_request(self, request: Request, response: Response):
        """Log request details for monitoring"""
        client_id = self.get_client_id(request)
        
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_id} - Status: {response.status_code}"
        )

# Global instances
api_response = ApiResponse()
input_validator = InputValidator()
security_middleware = SecurityMiddleware()

# Decorator for standardized responses
def api_endpoint(func):
    """Decorator to wrap API endpoints with standardized response format"""
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            
            # If result is already a JSONResponse (error), return it
            if isinstance(result, JSONResponse):
                return result
            
            # Wrap successful result
            return api_response.success(data=result)
            
        except HTTPException as e:
            return api_response.error(
                error=str(e.detail),
                error_code=e.status_code,
                status_code=e.status_code
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return api_response.error(
                error="Internal server error",
                error_code="INTERNAL_ERROR",
                status_code=500
            )
    
    return wrapper

# Middleware for rate limiting and security
async def security_middleware_func(request: Request, call_next):
    """FastAPI middleware for security checks"""
    
    # Check rate limit
    if not await security_middleware.check_rate_limit(request):
        return api_response.error(
            error="Rate limit exceeded",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )
    
    # Process request
    response = await call_next(request)
    
    # Log request
    await security_middleware.log_request(request, response)
    
    return response

# Utility functions for common validations
def validate_and_sanitize_inputs(**kwargs) -> Dict[str, Any]:
    """Validate and sanitize multiple inputs at once"""
    validated = {}
    
    for key, value in kwargs.items():
        if key == "symbol":
            validated[key] = input_validator.validate_symbol(value)
        elif key == "exchange":
            validated[key] = input_validator.validate_exchange(value)
        elif key == "timeframe":
            validated[key] = input_validator.validate_timeframe(value)
        elif key == "limit":
            validated[key] = input_validator.validate_limit(value)
        else:
            validated[key] = value
    
    return validated

# Error handling utilities
def handle_api_error(error: Exception, context: str = "") -> JSONResponse:
    """Handle API errors with proper logging and response"""
    logger.error(f"API Error in {context}: {str(error)}")
    
    if isinstance(error, HTTPException):
        return api_response.error(
            error=str(error.detail),
            error_code=str(error.status_code),
            status_code=error.status_code
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "message": "Internal server error",
                "code": "INTERNAL_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

def create_error_response(
    error: str,
    error_code: str = "GENERIC_ERROR",
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400
) -> JSONResponse:
    """Create a standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "message": error,
                "code": error_code,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

def api_response(data: Any = None, message: str = "Success", success: bool = True) -> Dict[str, Any]:
    """Create a standardized API response"""
    return {
        "success": success,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }

def input_validator(**kwargs) -> Dict[str, Any]:
    """Validate input parameters"""
    return kwargs
