"""
Authentication dependencies
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging
import os
from .database_unified import get_db, User, UserSession
from .security import SECRET_KEY, ALGORITHM

logger = logging.getLogger(__name__)
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
):
    """Get current user from token.
    Accepts either username or user id in the JWT 'sub' claim for backward compatibility.
    Returns user as dict for compatibility with existing code.
    If no credentials provided, tries to find tester2 user as fallback (for development/testing).
    """
    # If no credentials provided, check if we're in development mode
    if credentials is None:
        # Only allow guest/tester fallback in development mode
        debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        allow_guest = os.getenv("ALLOW_GUEST_ACCESS", "false").lower() == "true"
        
        if debug_mode and allow_guest:
            try:
                # Try to find tester2 user as fallback (development only)
                default_user = db.query(User).filter(User.username == "tester2").first()
                if default_user and default_user.is_active:
                    logger.warning(f"⚠️ DEVELOPMENT MODE: Using tester2 user as fallback: {default_user.username}")
                    return {
                        "id": default_user.id,
                        "username": default_user.username,
                        "email": default_user.email,
                        "is_active": default_user.is_active,
                        "role": default_user.role,
                        "user_id": default_user.id
                    }
            except Exception as e:
                logger.debug(f"Could not find tester2 user: {e}")
            
            # Guest user fallback (development only)
            logger.warning("⚠️ DEVELOPMENT MODE: Using guest user (unauthenticated access)")
            return {
                "id": 1,
                "username": "guest",
                "email": "guest@example.com",
                "is_active": True,
                "role": "user",
                "user_id": 1
            }
        else:
            # Production mode: require authentication
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        jti = payload.get("jti")  # Session ID (JWT ID)
        if subject is None:
            raise credentials_exception
        
        # Validate session if jti is present
        if jti:
            session = None
            # Query session - use raw SQL to avoid SQLite parameterized LIMIT/OFFSET issue
            # Since session_token is unique, we'll only get 0 or 1 result
            # Retry logic for database connection issues
            for attempt in range(2):  # Try twice
                try:
                    # Check database connection first
                    try:
                        db.execute(text("SELECT 1"))
                    except Exception as conn_error:
                        logger.debug(f"Database connection check failed (attempt {attempt + 1}): {conn_error}")
                        if attempt == 0:
                            # Refresh connection on first failure
                            try:
                                db.rollback()
                            except Exception:
                                pass
                            continue
                        else:
                            # On second failure, log and continue without session validation
                            logger.warning(f"Database connection failed after retry, skipping session validation: {conn_error}")
                            break
                    
                    # Use raw SQL query to avoid SQLite LIMIT/OFFSET parameterization issues
                    result = db.execute(
                        text("SELECT id FROM user_sessions WHERE session_token = :token AND is_active = 1"),
                        {"token": jti}
                    ).fetchone()
                    
                    if result:
                        # Get UserSession by ID using all() to avoid LIMIT/OFFSET issues
                        session_id = result[0]  # Get first column (id)
                        sessions = db.query(UserSession).filter(UserSession.id == session_id).all()
                        session = sessions[0] if sessions else None
                        break  # Success, exit retry loop
                    else:
                        session = None
                        break  # No result found, exit retry loop
                except Exception as e:
                    # Fallback to ORM query if raw SQL fails - use all() to avoid LIMIT/OFFSET
                    logger.debug(f"Raw SQL query failed (attempt {attempt + 1}), using ORM fallback: {e}")
                    try:
                        sessions = db.query(UserSession).filter(
                            UserSession.session_token == jti,
                            UserSession.is_active == True
                        ).all()
                        session = sessions[0] if sessions else None
                        if session:
                            break  # Success, exit retry loop
                    except Exception as orm_error:
                        logger.debug(f"ORM query also failed (attempt {attempt + 1}): {orm_error}")
                        if attempt == 0:
                            # Try refreshing connection
                            try:
                                db.rollback()
                            except Exception:
                                pass
                            continue
                        else:
                            # On second failure, log warning but don't fail the request
                            logger.warning(f"Session lookup failed after retry: {orm_error}")
                            break
            
            if not session:
                logger.warning(f"Session not found or inactive: {jti} (after retries)")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or invalidated. Please login again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check if session is expired
            # Handle None case defensively (shouldn't happen but SQLite can be unpredictable)
            current_time = datetime.utcnow()
            if session.expires_at is None:
                logger.warning(f"Session has no expiration date: {jti}, treating as expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or invalidated. Please login again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if session.expires_at < current_time:
                logger.warning(f"Session expired: {jti}")
                # Use ORM update to avoid SQLite parameter binding issues
                try:
                    session.is_active = False
                    db.commit()
                except Exception as expire_error:
                    logger.warning(f"Failed to deactivate expired session: {expire_error}")
                    db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired. Please login again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Update last activity - gracefully handle SQLite connection issues
            # This is non-critical, so we'll try but not fail the request if it doesn't work
            try:
                # Check if db connection is still valid
                try:
                    db.execute(text("SELECT 1"))
                except Exception as conn_check:
                    logger.debug(f"Database connection check failed (non-critical): {conn_check}")
                    # Skip update if connection is bad - don't return, continue with request
                    pass
                else:
                    # Use raw SQL with string conversion for SQLite datetime compatibility
                    # SQLite doesn't handle datetime objects well in parameterized queries
                    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S.%f')
                    try:
                        db.execute(
                            text("UPDATE user_sessions SET last_activity = :activity WHERE id = :session_id"),
                            {"activity": current_time_str, "session_id": session.id}
                        )
                        db.commit()
                    except Exception as sql_error:
                        # If raw SQL fails, try ORM as fallback
                        logger.debug(f"Raw SQL update failed, trying ORM: {sql_error}")
                        try:
                            session.last_activity = current_time
                            db.commit()
                        except Exception as orm_error:
                            # Both methods failed, log and continue
                            logger.debug(f"ORM update also failed (non-critical): {orm_error}")
                            db.rollback()
            except Exception as update_error:
                # SQLite connection/datetime issues - catch and continue
                import sqlalchemy.exc as sa_exc
                error_types = (sa_exc.InterfaceError, sa_exc.OperationalError, 
                              sa_exc.ProgrammingError, SystemError, TypeError)
                if isinstance(update_error, error_types):
                    logger.debug(f"SQLite connection/datetime issue (non-critical): {update_error}")
                else:
                    logger.debug(f"Could not update last_activity (non-critical): {update_error}")
                try:
                    db.rollback()
                except Exception:
                    pass  # Ignore rollback errors
                # Continue - the request should succeed even if activity update fails
    except HTTPException:
        raise
    except JWTError:
        raise credentials_exception

    # Try resolving subject as user id first, then as username
    user = None
    user_dict = None
    
    try:
        # If subject looks like an int id
        if isinstance(subject, str) and subject.isdigit():
            try:
                user = db.query(User).filter(User.id == int(subject)).first()
            except Exception as e:
                logger.warning(f"Error querying user by id {subject}: {e}")
                user = None
    except Exception as e:
        logger.warning(f"Error parsing subject as id: {e}")
        user = None

    if user is None:
        # Fallback to username - use explicit column selection to avoid IndexError
        try:
            # Try full object query first
            user = db.query(User).filter(User.username == str(subject)).first()
        except (IndexError, AttributeError) as e:
            # If IndexError occurs, try explicit column selection
            logger.warning(f"IndexError querying user by username, trying explicit columns: {e}")
            try:
                result = db.query(
                    User.id,
                    User.username,
                    User.email,
                    User.is_active,
                    User.role
                ).filter(User.username == str(subject)).first()
                
                if result:
                    user_dict = {
                        "id": result[0],
                        "username": result[1],
                        "email": result[2],
                        "is_active": result[3],
                        "role": result[4]
                    }
            except Exception as e2:
                logger.error(f"Error querying user by username with explicit columns: {e2}", exc_info=True)
        except Exception as e:
            logger.error(f"Error querying user by username {subject}: {e}", exc_info=True)
            user = None

    # Build return dict
    if user_dict:
        return {
            **user_dict,
            "user_id": user_dict["id"],
            "session_id": jti if jti else None
        }
    elif user:
        # Return as dict for compatibility
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "role": user.role,
            "user_id": user.id,  # Alias for compatibility
            "session_id": jti if jti else None  # Include session ID
        }
    else:
        raise credentials_exception

def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Get current active user"""
    if isinstance(current_user, dict):
        if not current_user.get("is_active", True):
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    else:
        # Handle User object (backward compatibility)
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_active": current_user.is_active,
            "role": current_user.role,
            "user_id": current_user.id
        }

# Optional auth: returns None if no/invalid token instead of raising
def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
):
    """Optionally retrieve current user. If no/invalid token, return None."""
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            return None
    except JWTError:
        return None

    user = None
    try:
        if isinstance(subject, str) and subject.isdigit():
            try:
                user = db.query(User).filter(User.id == int(subject)).first()
            except Exception as e:
                # Log but don't fail - try username lookup instead
                pass
        if user is None:
            try:
                user = db.query(User).filter(User.username == str(subject)).first()
            except Exception as e:
                # If both queries fail, return None
                return None
    except Exception as e:
        # Catch any other exceptions and return None
        return None
    
    if user:
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "role": user.role,
            "user_id": user.id
        }
    return None
