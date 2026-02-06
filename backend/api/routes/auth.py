"""
Authentication API routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Form
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime, timedelta
import secrets
import hashlib
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr
import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from services.otp_service import otp_service

logger = logging.getLogger(__name__)

from core.database_unified import SessionLocal as UnifiedSession, get_db, User, OTPVerification, UserSession
from core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    verify_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
import uuid
from fastapi import Request
from core.auth_dependencies import get_current_active_user
from schemas.auth import (
    UserCreate, 
    UserResponse, 
    UserLogin, 
    Token, 
    PasswordReset,
    PasswordResetConfirm,
    ChangePassword
)

router = APIRouter()
# ===== Password reset (forgot password) minimal implementation =====

# In-memory OTP store for password reset (single-process). Replace with DB/OTP service if available.
_RESET_OTP_STORE: Dict[str, Dict] = {}

def _now_utc() -> datetime:
    return datetime.utcnow()

def _generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"

class ForgotPasswordRequest(BaseModel):
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None

class VerifyResetOtpRequest(BaseModel):
    identifier: str  # email or mobile
    otp: str

class ResetPasswordRequest(BaseModel):
    identifier: str  # email or mobile
    otp: str
    new_password: str

# ===== Auth OTP send/verify =====
class SendOTPRequest(BaseModel):
    phone_or_email: str
    purpose: str = "login"
    is_email: bool = False

class VerifyOTPRequest(BaseModel):
    phone_or_email: str
    otp: str
    purpose: str = "login"

@router.post("/send-otp")
async def auth_send_otp(payload: SendOTPRequest):
    try:
        result = await otp_service.send_otp(payload.phone_or_email, payload.purpose, payload.is_email)

        # Normalize tuple response (ok, msg) if any backend returns tuples
        if isinstance(result, tuple) and len(result) >= 2:
            ok, msg = result[0], result[1]
            if ok:
                return {
                    "success": True,
                    "status": "success",
                    "message": msg,
                    "timestamp": datetime.utcnow().isoformat()
                }
            raise HTTPException(status_code=400, detail=msg)

        if result.get("success"):
            return {
                "success": True,
                "status": "success",
                "message": result.get("message", "OTP sent"),
                "timestamp": datetime.utcnow().isoformat()
            }
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to send OTP"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send-otp endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {e}")

@router.post("/verify-otp")
async def auth_verify_otp(payload: VerifyOTPRequest):
    try:
        result = otp_service.verify_otp(payload.phone_or_email, payload.otp, payload.purpose)

        # Normalize tuple or dict
        if isinstance(result, tuple) and len(result) >= 2:
            ok, msg = result[0], result[1]
            if not ok:
                raise HTTPException(status_code=400, detail=msg or "Invalid OTP")
            return {
                "success": True,
                "message": msg or "OTP verified successfully"
            }

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Invalid OTP"))

        purpose = (payload.purpose or "").strip().lower()

        identifier = (payload.phone_or_email or "").strip()
        candidates = [identifier]
        if "@" not in identifier:
            formatted = otp_service._format_phone_number(identifier)
            if formatted and formatted not in candidates:
                candidates.append(formatted)
            if identifier.startswith("+") and identifier[1:] not in candidates:
                candidates.append(identifier[1:])
            if not identifier.startswith("+") and f"+{identifier}" not in candidates:
                candidates.append(f"+{identifier}")

        # For signup/register OTP verification:
        # - Do NOT create a user here.
        # - If the user already exists, return an explicit error.
        # - Otherwise return success (frontend can proceed to /register).
        if purpose in {"signup", "register", "registration"}:
            db = UnifiedSession()
            try:
                existing = db.query(User).filter(
                    (User.email.in_(candidates)) |
                    (User.mobile_number.in_(candidates))
                ).first()
                if existing:
                    raise HTTPException(status_code=409, detail="User already exists")
                return {
                    "success": True,
                    "message": result.get("message", "OTP verified successfully")
                }
            finally:
                db.close()

        # For login OTP verification, user must exist (continue normal flow)
        db = UnifiedSession()
        try:
            user = db.query(User).filter(
                (User.email.in_(candidates)) |
                (User.mobile_number.in_(candidates))
            ).first()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Invalidate all previous sessions for this user
            db.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.is_active == True
            ).update({"is_active": False})
            db.commit()
            
            # Create new session
            session_id = str(uuid.uuid4())
            session_token = str(uuid.uuid4())
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            
            new_session = UserSession(
                id=session_id,
                user_id=user.id,
                session_token=session_token,
                is_active=True,
                expires_at=datetime.utcnow() + refresh_token_expires,
                last_activity=datetime.utcnow()
            )
            db.add(new_session)
            db.commit()
            
            access_token = create_access_token(
                data={"sub": str(user.id)}, 
                expires_delta=access_token_expires,
                jti=session_token
            )
            refresh_token = create_refresh_token(
                data={"sub": str(user.id)},
                jti=session_token
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify OTP: {e}")

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    """Generate an OTP for password reset and send it via email/SMS."""
    identifier = (payload.email or payload.mobile_number or "").strip()
    if not identifier:
        raise HTTPException(status_code=422, detail="Provide email or mobile_number")

    # Determine if identifier is email or mobile
    is_email = "@" in identifier
    
    try:
        # Use OTP service to generate, store, and send OTP
        try:
            result = await otp_service.send_otp(
                phone_or_email=identifier,
                purpose="password_reset",
                is_email=is_email
            )
        except Exception as otp_error:
            logger.error(f"OTP service exception: {otp_error}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"OTP service error: {str(otp_error)}")
        
        if result and result.get("success"):
            # Get normalized identifier from result (this is what was stored in DB)
            stored_identifier = result.get("phone_or_email", identifier)
            logger.info(f"✅ OTP sent successfully. Original identifier: {identifier}, Stored identifier: {stored_identifier}")
            
            # Also store in memory for backward compatibility (will be removed later)
            # Store with BOTH original and normalized identifiers
            otp = result.get("otp", "")
            if otp:
                logger.info(f"📝 Storing OTP in memory store for identifier: {identifier}, OTP: {otp}")
                _RESET_OTP_STORE[identifier] = {
                    "otp": otp,
                    "expires_at": _now_utc() + timedelta(minutes=10),
                    "attempts": 0,
                }
                # Also store with normalized identifier if different
                if stored_identifier != identifier:
                    logger.info(f"📝 Also storing in memory with normalized identifier: {stored_identifier}")
                    _RESET_OTP_STORE[stored_identifier] = {
                        "otp": otp,
                        "expires_at": _now_utc() + timedelta(minutes=10),
                        "attempts": 0,
                    }
            
            return {
                "success": True,
                "status": "success",
                "message": f"OTP sent to your {'email' if is_email else 'mobile number'}",
                "identifier": identifier,
                "stored_identifier": stored_identifier,  # Return what was stored in DB
                "ttl_seconds": 600,
                "method": "email" if is_email else "sms",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            error_msg = result.get("message", "Failed to send OTP") if result else "OTP service returned no result"
            logger.error(f"OTP service failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in forgot_password: {e}")
        # Fallback: Generate OTP and store in memory (for development/testing)
        otp = _generate_otp()
        _RESET_OTP_STORE[identifier] = {
            "otp": otp,
            "expires_at": _now_utc() + timedelta(minutes=10),
            "attempts": 0,
        }
        logger.warning(f"Using fallback OTP storage. OTP for {identifier}: {otp} (for testing only)")
        return {
            "success": True,
            "status": "success",
            "message": f"OTP generated (check logs for testing). Configure email/SMS for production.",
            "identifier": identifier,
            "ttl_seconds": 600,
            "method": "email" if is_email else "sms",
            "otp": otp,  # Only for development - remove in production
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/verify-reset-otp")
async def verify_reset_otp(payload: VerifyResetOtpRequest):
    """Verify OTP for password reset - checks database first, then in-memory store"""
    identifier = payload.identifier.strip()
    otp = payload.otp.strip()
    
    logger.info(f"🔍 VERIFY OTP REQUEST:")
    logger.info(f"   Frontend sent - Identifier: '{identifier}', OTP: '{otp}' (length: {len(otp)})")
    
    try:
        # First, try to verify using OTP service (database)
        # The OTP service will normalize the identifier automatically
        logger.info(f"   Step 1: Attempting database verification...")
        verify_result = otp_service.verify_otp(
            phone_or_email=identifier,
            otp=otp,
            purpose="password_reset"
        )
        logger.info(f"   Database verification result: {verify_result.get('success')}, Message: {verify_result.get('message')}")
        
        if verify_result.get("success"):
            # OTP verified successfully in database
            logger.info(f"OTP verified successfully for {identifier} via database")
            return {
                "success": True,
                "status": "success",
                "message": "OTP verified",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # If database verification failed, try in-memory store (fallback for backward compatibility)
        error_msg = verify_result.get("message", "OTP not found or expired")
        logger.warning(f"Database OTP verification failed for {identifier}, trying in-memory store. Error: {error_msg}")
        
        # Try exact match first
        entry = _RESET_OTP_STORE.get(identifier)
        
        # Try alternative formats in memory store (for backward compatibility)
        if not entry and "@" not in identifier:
            if identifier.startswith("+"):
                entry = _RESET_OTP_STORE.get(identifier[1:])
            elif not identifier.startswith("+"):
                # Try with +91 prefix for 10-digit Indian numbers
                if len(identifier) == 10 and identifier[0] in "6789":
                    entry = _RESET_OTP_STORE.get(f"+91{identifier}")
                # Try with + prefix
                entry = entry or _RESET_OTP_STORE.get(f"+{identifier}")
        
        if not entry:
            logger.error(f"OTP verification failed: {error_msg} for identifier: {identifier}")
            raise HTTPException(status_code=400, detail=f"{error_msg}. Please request a new OTP.")
        
        if entry["expires_at"] < _now_utc():
            _RESET_OTP_STORE.pop(identifier, None)
            raise HTTPException(status_code=400, detail="OTP expired. Please request a new OTP.")
        
        entry["attempts"] += 1
        if entry["attempts"] > 5:
            _RESET_OTP_STORE.pop(identifier, None)
            raise HTTPException(status_code=429, detail="Too many attempts. Please request a new OTP.")
        
        if otp != entry["otp"]:
            raise HTTPException(status_code=400, detail="Invalid OTP. Please check and try again.")
        
        logger.info(f"OTP verified successfully for {identifier} via in-memory store")
        return {
            "success": True,
            "status": "success",
            "message": "OTP verified",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying reset OTP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to verify OTP: {str(e)}")

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password after OTP verification"""
    identifier = payload.identifier.strip()
    otp = payload.otp.strip()
    
    logger.info(f"🔐 RESET PASSWORD REQUEST:")
    logger.info(f"   Identifier: '{identifier}', OTP length: {len(otp)}")
    
    # Verify OTP - check if it was already verified in verify-reset-otp step
    # or verify it now if it hasn't been verified yet
    otp_valid = False
    try:
        # First, check if OTP was already verified (from verify-reset-otp step)
        # Normalize identifier for database lookup
        normalized_id = identifier
        if "@" not in identifier:
            formatted = otp_service._format_phone_number(identifier)
            if formatted:
                normalized_id = formatted
        
        db_otp = UnifiedSession()
        try:
            # Find OTP record (including verified and expired ones) that matches the OTP code
            # If OTP was already verified, we allow it even if expired (verification already happened)
            otp_record = db_otp.query(OTPVerification).filter(
                OTPVerification.phone_or_email == normalized_id,
                OTPVerification.purpose == "password_reset",
                OTPVerification.otp == otp
            ).order_by(OTPVerification.created_at.desc()).first()
            
            if otp_record:
                # Check if OTP is expired
                is_expired = otp_record.expires_at < datetime.utcnow()
                
                if otp_record.is_verified:
                    # OTP was already verified - allow password reset even if expired
                    # (verification already happened, so expiration doesn't matter)
                    if is_expired:
                        logger.info(f"✅ OTP was already verified for {identifier} (expired but verification was done), proceeding with password reset")
                    else:
                        logger.info(f"✅ OTP was already verified for {identifier}, proceeding with password reset")
                    otp_valid = True
                elif not is_expired:
                    # OTP exists, not verified yet, and not expired - verify it now
                    logger.info(f"   OTP found but not verified yet, verifying now...")
                    verify_result = otp_service.verify_otp(
                        phone_or_email=identifier,
                        otp=otp,
                        purpose="password_reset"
                    )
                    if verify_result.get("success"):
                        logger.info(f"✅ OTP verified successfully for {identifier}")
                        otp_valid = True
                    else:
                        logger.warning(f"   OTP verification failed: {verify_result.get('message')}")
                else:
                    # OTP exists but expired and not verified
                    logger.error(f"❌ OTP expired and not verified for {identifier}")
                    logger.error(f"   Expires: {otp_record.expires_at}, Now: {datetime.utcnow()}")
            else:
                # OTP not found in database, try to verify (might be in memory store)
                logger.info(f"   OTP not found in database, trying verification...")
                verify_result = otp_service.verify_otp(
                    phone_or_email=identifier,
                    otp=otp,
                    purpose="password_reset"
                )
                if verify_result.get("success"):
                    logger.info(f"✅ OTP verified successfully for {identifier}")
                    otp_valid = True
                else:
                    # Fallback to in-memory store
                    logger.warning(f"   OTP verification failed, trying in-memory store...")
                    entry = _RESET_OTP_STORE.get(identifier)
                    if not entry:
                        # Try alternative formats
                        if "@" not in identifier:
                            if identifier.startswith("+"):
                                entry = _RESET_OTP_STORE.get(identifier[1:])
                            elif len(identifier) == 10 and identifier[0] in "6789":
                                entry = _RESET_OTP_STORE.get(f"+91{identifier}")
                            entry = entry or _RESET_OTP_STORE.get(f"+{identifier}")
                    
                    if entry and entry.get("otp") == otp:
                        if entry.get("expires_at", _now_utc()) >= _now_utc():
                            logger.info(f"✅ OTP found in in-memory store for {identifier}")
                            otp_valid = True
                        else:
                            logger.error(f"❌ OTP expired in in-memory store for {identifier}")
                    else:
                        logger.error(f"❌ OTP not found in in-memory store for {identifier}")
        finally:
            db_otp.close()
        
        if not otp_valid:
            raise HTTPException(status_code=400, detail="OTP invalid or expired. Please verify OTP again.")
                    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying OTP in reset_password: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"OTP verification failed: {str(e)}")

    # Lookup user by email or mobile and update password
    # User is already imported from core.database at the top
    user_q = None
    lookup_identifier = identifier  # Use the normalized identifier from OTP verification
    tried_formats = [lookup_identifier]  # Track formats tried for error message
    
    logger.info(f"🔍 Looking up user with identifier: '{lookup_identifier}'")
    
    if "@" in lookup_identifier:
        # Email lookup
        user_q = db.query(User).filter(User.email == lookup_identifier).first()
        logger.info(f"   Email lookup result: {'Found' if user_q else 'Not found'}")
    else:
        # Mobile number lookup - try multiple formats
        mobile_formats = [lookup_identifier]
        
        # If identifier is normalized (starts with +), try without +
        if lookup_identifier.startswith("+"):
            mobile_formats.append(lookup_identifier[1:])
            # Try with country code variations
            if lookup_identifier.startswith("+91"):
                mobile_formats.append(lookup_identifier[3:])  # Remove +91
            elif lookup_identifier.startswith("+1"):
                mobile_formats.append(lookup_identifier[2:])  # Remove +1
        else:
            # If identifier doesn't start with +, try with +
            mobile_formats.append(f"+{lookup_identifier}")
            # Try with country codes
            if len(lookup_identifier) == 10 and lookup_identifier[0] in "6789":
                mobile_formats.append(f"+91{lookup_identifier}")
            mobile_formats.append(f"+1{lookup_identifier}")
        
        tried_formats = mobile_formats
        logger.info(f"   Trying mobile number formats: {mobile_formats}")
        
        # Try each format
        for mobile_format in mobile_formats:
            user_q = db.query(User).filter(User.mobile_number == mobile_format).first()
            if user_q:
                logger.info(f"   ✅ Found user with mobile number format: '{mobile_format}'")
                break
        
        if not user_q:
            # Fallback: try username
            logger.info(f"   Mobile lookup failed, trying username...")
            user_q = db.query(User).filter(User.username == lookup_identifier).first()
            if user_q:
                logger.info(f"   ✅ Found user with username: '{lookup_identifier}'")
            tried_formats.append(f"username: {lookup_identifier}")

    if not user_q:
        logger.error(f"❌ User not found for identifier: '{lookup_identifier}'")
        logger.error(f"   Tried formats: {tried_formats}")
        # Also log all users in database for debugging (be careful in production)
        all_users = db.query(User).all()
        logger.info(f"   Total users in database: {len(all_users)}")
        if len(all_users) <= 10:  # Only log if small number of users
            for u in all_users:
                logger.info(f"      - User: {u.username}, Email: {u.email}, Mobile: {u.mobile_number}")
        raise HTTPException(status_code=404, detail=f"User not found. Please ensure you're using the same email or mobile number you registered with.")

    # Hash password using existing utility (already imported at top)
    user_q.password_hash = get_password_hash(payload.new_password)
    db.commit()
    db.refresh(user_q)
    
    logger.info(f"✅ Password reset successful for user: {user_q.username} (ID: {user_q.id}, Email: {user_q.email}, Mobile: {user_q.mobile_number})")
    
    # Clear OTP from in-memory store (if exists)
    _RESET_OTP_STORE.pop(identifier, None)
    # Also try normalized format
    if "@" not in identifier:
        normalized = otp_service._format_phone_number(identifier)
        if normalized and normalized != identifier:
            _RESET_OTP_STORE.pop(normalized, None)
    
    return {
        "success": True,
        "status": "success",
        "message": "Password reset successful",
        "timestamp": datetime.utcnow().isoformat()
    }

# ===== Registration with dual OTP (SMS + Email) =====

class RegisterInitRequest(BaseModel):
    username: str
    email: EmailStr
    mobile_number: str
    password: str

class RegisterVerifyRequest(BaseModel):
    username: str
    email: EmailStr
    mobile_number: str
    password: str
    otp_sms: str
    otp_email: str

@router.post("/register/init")
async def register_init(payload: RegisterInitRequest):
    """Initiate registration: send OTP to mobile and email (purpose='register')."""
    try:
        # Send SMS OTP
        sms_result = await otp_service.send_otp(payload.mobile_number, purpose="register", is_email=False)
        # Send Email OTP
        email_result = await otp_service.send_otp(payload.email, purpose="register", is_email=True)

        # Normalize possible tuple responses
        def _ok(res):
            if isinstance(res, tuple) and len(res) >= 2:
                return bool(res[0])
            return bool(res.get("success"))

        success = _ok(sms_result) and _ok(email_result)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to send one or more OTPs")

        return {
            "success": True,
            "message": "Registration OTPs sent to mobile and email",
            "mobile": payload.mobile_number,
            "email": payload.email,
            "ttl_seconds": 600
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate registration: {e}")

@router.post("/register/verify", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_verify(payload: RegisterVerifyRequest, db: Session = Depends(get_db)):
    """Verify both OTPs and create the user."""
    try:
        # Validate OTPs
        sms_ok = otp_service.verify_otp(payload.mobile_number, payload.otp_sms, purpose="register").get("success")
        email_ok = otp_service.verify_otp(payload.email, payload.otp_email, purpose="register").get("success")
        if not (sms_ok and email_ok):
            raise HTTPException(status_code=400, detail="Invalid or expired OTP(s)")

        # Check duplicates
        if db.query(User).filter(User.username == payload.username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        if db.query(User).filter(User.mobile_number == payload.mobile_number).first():
            raise HTTPException(status_code=400, detail="Mobile number already registered")

        # Create user
        hashed_password = get_password_hash(payload.password)
        db_user = User(
            username=payload.username,
            email=payload.email,
            mobile_number=payload.mobile_number,
            password_hash=hashed_password,
            is_active=True,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Optionally send welcome email
        send_welcome_email(payload.email, payload.username, payload.password)

        return UserResponse.from_orm(db_user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to complete registration: {e}")

def send_welcome_email(user_email: str, username: str, password: str):
    """Send welcome email with login credentials"""
    try:
        # Email configuration
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        email_address = os.getenv('EMAIL_ADDRESS', '')
        email_password = os.getenv('EMAIL_PASSWORD', '')
        
        if not email_address or not email_password:
            print("⚠️ Email credentials not configured. Skipping email send.")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = email_address
        msg['To'] = user_email
        msg['Subject'] = "Welcome to Trader AI - Your Account Details"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Welcome to Trader AI!</h2>
            <p>Your account has been successfully created.</p>
            
            <h3>Login Details:</h3>
            <ul>
                <li><strong>Username:</strong> {username}</li>
                <li><strong>Email:</strong> {user_email}</li>
                <li><strong>Password:</strong> {password}</li>
            </ul>
            
            <h3>Next Steps:</h3>
            <ol>
                <li>Login to your account at: <a href="http://13.127.66.147:3000">http://13.127.66.147:3000</a></li>
                <li>Change your password for security</li>
                <li>Complete your profile setup</li>
            </ol>
            
            <p><strong>Security Note:</strong> Please change your password after first login for security reasons.</p>
            
            <p>Best regards,<br>Trader AI Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_address, email_password)
        text = msg.as_string()
        server.sendmail(email_address, user_email, text)
        server.quit()
        
        print(f"OK Welcome email sent to {user_email}")
        return True
        
    except Exception as e:
        print(f"ERROR Error sending email: {e}")
        return False

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if username already exists
        if db.query(User).filter(User.username == user.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if mobile number already exists (if provided)
        if user.mobile_number and db.query(User).filter(User.mobile_number == user.mobile_number).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mobile number already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            mobile_number=user.mobile_number,
            password_hash=hashed_password,
            is_active=user.is_active
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Send welcome email with login credentials
        send_welcome_email(user.email, user.username, user.password)
        
        return UserResponse.from_orm(db_user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin = Body(None),
    username: str = Form(None),
    password: str = Form(None),
    db: Session = Depends(get_db)
):
    """Login user and return access token"""
    try:
        # Support both JSON body (UserLogin) and form data
        if user_credentials and user_credentials.username and user_credentials.password:
            in_username = user_credentials.username
            in_password = user_credentials.password
        else:
            in_username = username
            in_password = password

        if not in_username or not in_password:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="username and password required")

        # Find user by username, email, or mobile number
        user = db.query(User).filter(
            (User.username == in_username) | 
            (User.email == in_username) | 
            (User.mobile_number == in_username)
        ).first()
        
        if not user or not verify_password(in_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Invalidate all previous sessions for this user (single session enforcement)
        db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).update({"is_active": False})
        db.commit()
        
        # Create new session
        session_id = str(uuid.uuid4())
        session_token = str(uuid.uuid4())  # JWT jti
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        new_session = UserSession(
            id=session_id,
            user_id=user.id,
            session_token=session_token,
            is_active=True,
            expires_at=datetime.utcnow() + refresh_token_expires,
            last_activity=datetime.utcnow()
        )
        db.add(new_session)
        db.commit()
        
        # Create tokens with session ID
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires,
            jti=session_token
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)},
            jti=session_token
        )
        
        # Update last_login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during login: {e}"
        )

@router.post("/login-form", response_model=Token)
async def login_user_form(
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user with form data (for frontend compatibility)"""
    try:
        # Try to parse JSON first
        try:
            json_data = await request.json()
            in_username = json_data.get("username")
            in_password = json_data.get("password")
        except Exception as e:
            # Fallback to form data
            form_data = await request.form()
            in_username = form_data.get("username")
            in_password = form_data.get("password")

        if not in_username or not in_password:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="username and password required")

        # Find user by username, email, or mobile number
        user = db.query(User).filter(
            (User.username == in_username) | 
            (User.email == in_username) | 
            (User.mobile_number == in_username)
        ).first()
        
        if not user or not verify_password(in_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Invalidate all previous sessions for this user (single session enforcement)
        db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).update({"is_active": False})
        db.commit()
        
        # Create new session
        session_id = str(uuid.uuid4())
        session_token = str(uuid.uuid4())  # JWT jti
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Get device info from request
        device_info = None
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", None)
        
        new_session = UserSession(
            id=session_id,
            user_id=user.id,
            session_token=session_token,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            expires_at=datetime.utcnow() + refresh_token_expires,
            last_activity=datetime.utcnow()
        )
        db.add(new_session)
        db.commit()
        
        # Create tokens with session ID
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires,
            jti=session_token
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)},
            jti=session_token
        )
        
        # Update last_login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ ERROR in login_user_form: {e}", exc_info=True)
        import traceback
        logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during login: {str(e)}"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("sub")
        jti = payload.get("jti")  # Session ID
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Validate session if jti is present
        if jti:
            session = db.query(UserSession).filter(
                UserSession.session_token == jti,
                UserSession.user_id == user.id,
                UserSession.is_active == True
            ).first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or invalidated"
                )
            
            # Check if session is expired
            if session.expires_at < datetime.utcnow():
                session.is_active = False
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired"
                )
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            db.commit()
        
        # Create new tokens with same session ID
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires,
            jti=jti if jti else None
        )
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id)},
            jti=jti if jti else None
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing token: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    user_id = current_user.get("id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user)

@router.put("/me", response_model=UserResponse)
async def update_user_info(
    user_update: dict,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    try:
        user_id = current_user.get("id")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update allowed fields
        if "email" in user_update:
            # Check if email is already taken by another user
            existing_user = db.query(User).filter(
                User.email == user_update["email"],
                User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            user.email = user_update["email"]
        
        if "is_active" in user_update:
            user.is_active = user_update["is_active"]
        
        db.commit()
        db.refresh(user)
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )

@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        user_id = current_user.get("id")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        if not verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.password_hash = get_password_hash(password_data.new_password)
        db.commit()
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing password: {str(e)}"
        )

@router.post("/logout")
async def logout_user(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout user - invalidates current session"""
    try:
        session_id = current_user.get("session_id")
        if session_id:
            # Mark session as inactive
            session = db.query(UserSession).filter(
                UserSession.session_token == session_id
            ).first()
            if session:
                session.is_active = False
                db.commit()
                logger.info(f"Session {session_id} invalidated for user {current_user.get('id')}")
        
        return {"message": "Successfully logged out", "success": True}
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return {"message": "Logged out (session may not have been invalidated)", "success": True}

# OAuth2 compatible endpoint for form-based login
@router.post("/token", response_model=Token)
async def login_for_access_token(
    username: str = Form(None),
    password: str = Form(None),
    user_credentials: UserLogin = Body(None),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible login endpoint"""
    # Accept JSON or form
    if user_credentials and user_credentials.username and user_credentials.password:
        in_username = user_credentials.username
        in_password = user_credentials.password
    else:
        in_username = username
        in_password = password

    if not in_username or not in_password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="username and password required")

    user = db.query(User).filter(User.username == in_username).first()
    
    if not user or not verify_password(in_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Invalidate all previous sessions for this user
    db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_active == True
    ).update({"is_active": False})
    db.commit()
    
    # Create new session
    session_id = str(uuid.uuid4())
    session_token = str(uuid.uuid4())
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    new_session = UserSession(
        id=session_id,
        user_id=user.id,
        session_token=session_token,
        is_active=True,
        expires_at=datetime.utcnow() + refresh_token_expires,
        last_activity=datetime.utcnow()
    )
    db.add(new_session)
    db.commit()
    
    access_token = create_access_token(
        data={"sub": str(user.id)}, 
        expires_delta=access_token_expires,
        jti=session_token
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)},
        jti=session_token
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/verify-token")
async def verify_token(current_user: dict = Depends(get_current_active_user)):
    """Verify JWT token validity"""
    return {
        "success": True, 
        "valid": True, 
        "message": "Token is valid",
        "user_id": current_user.get("id"),
        "username": current_user.get("username")
    }
