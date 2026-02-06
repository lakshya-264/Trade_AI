"""
Request Filter Middleware
Handles unknown/invalid requests and improves logging
"""

import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RequestFilterMiddleware(BaseHTTPMiddleware):
    """Middleware to filter and handle unknown requests"""
    
    def __init__(self, app, allowed_hosts=None, block_suspicious=True):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or ["localhost", "127.0.0.1", "13.127.66.147"]
        self.block_suspicious = block_suspicious
        
        # Patterns for suspicious requests
        self.suspicious_patterns = [
            r'\.\./',  # Directory traversal
            r'<script',  # XSS attempts
            r'union\s+select',  # SQL injection
            r'exec\s*\(',  # Command injection
            r'eval\s*\(',  # Code injection
        ]
        
        # Known good API paths
        self.valid_api_paths = [
            r'^/api/',
            r'^/health$',
            r'^/docs$',
            r'^/redoc$',
            r'^/openapi\.json$',
            r'^/favicon\.ico$',
            r'^/static/',
            r'^/$',  # Root path
        ]
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract request info
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        
        # Check if request is suspicious
        is_suspicious = self._is_suspicious_request(path, user_agent)
        
        # Check if request is valid
        is_valid = self._is_valid_request(path)
        
        # Log all requests with details
        if is_suspicious:
            logger.warning(f"🚨 SUSPICIOUS REQUEST: {method} {path} from {client_ip} | UA: {user_agent[:100]}")
        elif not is_valid:
            logger.info(f"⚠️  UNKNOWN REQUEST: {method} {path} from {client_ip} | UA: {user_agent[:100]}")
        else:
            logger.info(f"✅ VALID REQUEST: {method} {path} from {client_ip}")
        
        # Block suspicious requests if enabled
        if self.block_suspicious and is_suspicious:
            return JSONResponse(
                status_code=403,
                content={"detail": "Request blocked for security reasons"}
            )
        
        # Handle invalid requests gracefully
        if not is_valid and not path.startswith('/api/'):
            # For non-API requests, return a simple response
            if path == '/favicon.ico':
                return Response(status_code=204)  # No content for favicon
            elif path == '/':
                return JSONResponse(
                    status_code=200,
                    content={
                        "message": "Trader AI Backend API",
                        "status": "running",
                        "docs": "/docs",
                        "health": "/health"
                    }
                )
            else:
                return JSONResponse(
                    status_code=404,
                    content={"detail": f"Endpoint {path} not found"}
                )
        
        # Process valid requests
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(f"📊 RESPONSE: {method} {path} -> {response.status_code} ({process_time:.3f}s)")
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"❌ ERROR: {method} {path} -> {str(e)} ({process_time:.3f}s)")
            
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
    
    def _is_suspicious_request(self, path: str, user_agent: str) -> bool:
        """Check if request is suspicious"""
        # Check for suspicious patterns in path
        for pattern in self.suspicious_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        
        # Check for suspicious user agents
        suspicious_ua_patterns = [
            r'scanner', r'bot', r'crawler', r'spider', r'wget', r'curl'
        ]
        
        for pattern in suspicious_ua_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True
        
        return False
    
    def _is_valid_request(self, path: str) -> bool:
        """Check if request path is valid"""
        for pattern in self.valid_api_paths:
            if re.match(pattern, path):
                return True
        return False
