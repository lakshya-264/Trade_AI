"""
Security utilities
"""
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
import hashlib
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import uuid
import numpy as np
from typing import Any

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
# Session expiration - configurable via environment variables
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

def _convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert NumPy types to native Python types for JSON serialization.
    This is a helper function used by the custom jsonable_encoder.
    """
    if obj is None:
        return None
    
    # Check for numpy types FIRST (before dict/list checks)
    try:
        # numpy.bool_ is the most common issue
        if isinstance(obj, np.bool_) or (hasattr(np, 'bool8') and isinstance(obj, np.bool8)):
            return bool(obj)
        
        if isinstance(obj, np.integer):
            return int(obj)
        
        if isinstance(obj, np.floating):
            return float(obj)
        
        if isinstance(obj, np.complexfloating):
            return complex(obj)
        
        if isinstance(obj, np.generic):
            try:
                result = obj.item()
                return _convert_numpy_types(result)
            except (AttributeError, ValueError, TypeError):
                if 'bool' in str(type(obj)).lower():
                    return bool(obj)
                elif 'int' in str(type(obj)).lower():
                    return int(obj)
                elif 'float' in str(type(obj)).lower():
                    return float(obj)
        
        if isinstance(obj, np.ndarray):
            return [_convert_numpy_types(item) for item in obj.tolist()]
    except Exception:
        pass
    
    # Check by type string as fallback
    try:
        type_str = str(type(obj))
        type_module = type(obj).__module__ if hasattr(type(obj), '__module__') else ''
        if 'numpy' in type_module.lower() or 'numpy' in type_str.lower():
            if hasattr(obj, 'item'):
                try:
                    return _convert_numpy_types(obj.item())
                except (AttributeError, ValueError, TypeError):
                    pass
            if 'bool' in type_str.lower():
                return bool(obj)
            elif 'int' in type_str.lower():
                return int(obj)
            elif 'float' in type_str.lower():
                return float(obj)
    except Exception:
        pass
    
    # Handle collections recursively
    if isinstance(obj, dict):
        return {key: _convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_numpy_types(item) for item in obj]
    
    return obj

def create_secure_app(lifespan=None):
    """Create secure FastAPI app with numpy type conversion support"""
    app = FastAPI(
        title="Trader AI Backend",
        version="1.0.0",
        description="Indian Stock Market Trading Platform",
        lifespan=lifespan
    )
    
    # Override jsonable_encoder to handle numpy types
    original_jsonable_encoder = jsonable_encoder
    
    def custom_jsonable_encoder(obj: Any, *args, **kwargs):
        """Custom encoder that converts numpy types before FastAPI's encoder"""
        # Convert numpy types first
        converted_obj = _convert_numpy_types(obj)
        # Then use FastAPI's encoder
        return original_jsonable_encoder(converted_obj, *args, **kwargs)
    
    # Monkey-patch FastAPI's jsonable_encoder
    import fastapi.encoders
    fastapi.encoders.jsonable_encoder = custom_jsonable_encoder
    
    return app

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using SHA256"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    """Get password hash using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta = None, jti: str = None):
    """Create access token - proper JWT token with session ID (jti)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add session ID (jti) for session management
    if jti:
        to_encode.update({"jti": jti})
    else:
        # Generate jti if not provided
        to_encode.update({"jti": str(uuid.uuid4())})
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, jti: str = None):
    """Create refresh token - proper JWT token with session ID (jti)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Add session ID (jti) for session management
    if jti:
        to_encode.update({"jti": jti})
    else:
        # Generate jti if not provided
        to_encode.update({"jti": str(uuid.uuid4())})
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_refresh_token(token: str):
    """Verify refresh token - proper JWT verification"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None

def check_rate_limit():
    """Check rate limit - simplified version"""
    return True
