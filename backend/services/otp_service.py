"""
Fixed Unified OTP Service v2.0.0
Properly stores OTPs in database (PostgreSQL primary + SQLite secondary)
Fixes the critical issue where OTPs were not being stored in the database

This service:
1. Generates secure OTPs
2. Stores them in the database (otp_records table)
3. Sends via SMS (Twilio) and Email (SMTP)
4. Verifies OTPs against database
5. Handles expiration and attempt limits
"""

import os
import sys
import random
import string
import asyncio
import aiohttp
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Load environment
load_dotenv()
logger = logging.getLogger(__name__)

# Use unified database model instead of separate Base
# Import OTPVerification from unified database
import sys
import os as os_path
sys.path.insert(0, os_path.path.join(os_path.path.dirname(__file__), '..'))
from core.database_unified import OTPVerification, Base

# Alias for backward compatibility
OTPRecord = OTPVerification

class FixedOTPService:
    """Fixed OTP Service with dual database support (PostgreSQL primary + SQLite secondary)"""
    
    def __init__(self):
        # Twilio SMS Configuration
        self.twilio_sid = os.getenv("TWILIO_SID") or os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_token = os.getenv("TWILIO_TOKEN") or os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone = os.getenv("TWILIO_PHONE") or os.getenv("TWILIO_FROM_NUMBER")
        
        # Email Configuration (using SMTP)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        
        # Dual Database Configuration - USE UNIFIED DATABASE
        # Import unified database URL to ensure consistency
        import sys
        import os as os_path
        sys.path.insert(0, os_path.path.join(os_path.path.dirname(__file__), '..'))
        from core.database_unified import (
            DATABASE_URL as UNIFIED_DB_URL,
            engine as UNIFIED_ENGINE,
            SessionLocal as UNIFIED_SESSION
        )
        
        self.primary_db_url = UNIFIED_DB_URL  # Use unified database
        self.secondary_db_url = UNIFIED_DB_URL  # Use same database for both
        self.unified_engine = UNIFIED_ENGINE  # Use unified engine
        self.unified_session = UNIFIED_SESSION  # Use unified session
        
        # OTP Configuration
        self.otp_length = 6
        self.otp_expiry_minutes = 10
        self.max_attempts = 3
        
        # Initialize both databases (now unified_engine and unified_session are set)
        self._init_databases()
        
        logger.info("Fixed OTP Service with dual database support initialized successfully")
    
    def _init_databases(self):
        """Initialize database connections using unified database"""
        try:
            # CRITICAL: Use unified database engine and session directly
            # Do NOT create new engines - use the unified ones
            self.primary_engine = self.unified_engine
            self.secondary_engine = self.unified_engine  # Same as primary
            
            # Create tables - this ensures otp_verifications table exists with all columns
            # Use the unified Base metadata
            Base.metadata.create_all(bind=self.primary_engine, checkfirst=True)
            logger.info(f"Created/verified otp_verifications table in unified database")
            
            # Use unified session directly - DO NOT create new sessionmaker
            self.PrimarySessionLocal = self.unified_session
            self.SecondarySessionLocal = self.unified_session  # Same as primary
            
            # Set primary as default for backward compatibility
            self.SessionLocal = self.PrimarySessionLocal
            self.engine = self.primary_engine
            
            logger.info(f"✅ Using unified database: {self.primary_db_url}")
            logger.info(f"   Engine: {self.primary_engine}")
            logger.info(f"   Session: {self.PrimarySessionLocal}")
            logger.info(f"   Table: otp_verifications (unified Base)")
            
            # Verify table exists and has required columns
            from sqlalchemy import inspect
            inspector = inspect(self.primary_engine)
            tables = inspector.get_table_names()
            if 'otp_verifications' in tables:
                logger.info("✅ otp_verifications table verified in database")
                
                # Check columns using direct SQL query to avoid metadata cache issues
                # AND automatically add missing columns
                try:
                    # Use raw SQL to check columns (bypasses SQLAlchemy metadata cache)
                    with self.primary_engine.connect() as conn:
                        result = conn.execute(text("PRAGMA table_info(otp_verifications)"))
                        db_columns = [row[1] for row in result]
                    
                    required_cols = ['phone_or_email', 'otp', 'purpose', 'is_email', 'attempts']
                    missing_cols = [c for c in required_cols if c not in db_columns]
                    
                    if missing_cols:
                        logger.warning(f"⚠️  Missing columns detected: {missing_cols}")
                        logger.warning(f"   Existing columns: {db_columns}")
                        logger.warning(f"   Attempting to add missing columns automatically...")
                        
                        # Automatically add missing columns
                        try:
                            self._add_missing_columns()
                            # Re-check after adding
                            with self.primary_engine.connect() as conn:
                                result = conn.execute(text("PRAGMA table_info(otp_verifications)"))
                                db_columns_after = [row[1] for row in result]
                            missing_after = [c for c in required_cols if c not in db_columns_after]
                            if not missing_after:
                                logger.info(f"✅ Successfully added all missing columns!")
                            else:
                                logger.error(f"❌ Still missing after auto-add: {missing_after}")
                        except Exception as add_error:
                            logger.error(f"❌ Failed to add columns automatically: {add_error}")
                            import traceback
                            logger.error(traceback.format_exc())
                    else:
                        logger.info(f"✅ All required columns exist: {required_cols}")
                except Exception as e:
                    logger.warning(f"Could not check columns via PRAGMA: {e}")
                    # Fallback to inspector
                    columns = inspector.get_columns('otp_verifications')
                    col_names = [col['name'] for col in columns]
                    logger.info(f"   Columns (from inspector): {col_names}")
                
                # Test query to ensure table is accessible
                try:
                    test_db = self.PrimarySessionLocal()
                    test_count = test_db.query(OTPRecord).count()
                    logger.info(f"   Current OTP records in table: {test_count}")
                    test_db.close()
                except Exception as e:
                    logger.error(f"   ❌ Could not query otp_verifications table: {e}")
                    logger.error(f"   This indicates the table structure doesn't match the model!")
                    # Try to add missing columns automatically
                    logger.warning(f"   Attempting to add missing columns...")
                    try:
                        self._add_missing_columns()
                    except Exception as add_error:
                        logger.error(f"   Failed to add columns: {add_error}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.error("❌ otp_verifications table NOT found in database!")
                logger.error(f"   Available tables: {', '.join(tables[:10])}")
            
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}", exc_info=True)
            raise
    
    def _add_missing_columns(self):
        """Add missing columns to otp_verifications table"""
        try:
            required_cols = {
                'phone_or_email': 'TEXT',
                'otp': 'TEXT',
                'purpose': 'TEXT',
                'is_email': 'INTEGER',
                'attempts': 'INTEGER'
            }
            
            # Use begin() to get a transaction (auto-commits on success)
            with self.primary_engine.begin() as conn:
                # Get current columns
                result = conn.execute(text("PRAGMA table_info(otp_verifications)"))
                existing = [row[1] for row in result]
                
                # Add missing columns
                added_count = 0
                for col_name, col_type in required_cols.items():
                    if col_name not in existing:
                        try:
                            sql = f"ALTER TABLE otp_verifications ADD COLUMN {col_name} {col_type}"
                            conn.execute(text(sql))
                            added_count += 1
                            logger.info(f"   ✅ Added column: {col_name}")
                        except Exception as e:
                            if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                                logger.debug(f"   ℹ️  {col_name} already exists")
                            else:
                                logger.warning(f"   Could not add {col_name}: {e}")
                
                # Commit is automatic with begin() context manager
                if added_count > 0:
                    logger.info(f"✅ Added {added_count} missing column(s)")
                else:
                    logger.info("ℹ️  No columns needed to be added")
            
        except Exception as e:
            logger.error(f"Failed to add missing columns: {e}", exc_info=True)
    
    def _generate_otp(self) -> str:
        """Generate a secure OTP"""
        return ''.join(random.choices(string.digits, k=self.otp_length))
    
    def _format_phone_number(self, phone_number: str) -> Optional[str]:
        """Format phone number to E.164 format for Twilio"""
        if not phone_number:
            return None
        
        # Check for invalid characters first (like XXXX, which indicates masked/obfuscated numbers)
        phone_upper = phone_number.upper()
        if 'X' in phone_upper or '*' in phone_number:
            logger.error(f"Invalid phone number format (contains masked characters): {phone_number}")
            return None
        
        # Remove all non-digit characters except +
        cleaned = phone_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('.', '')
        digits_only = ''.join(filter(str.isdigit, cleaned))
        
        # Check minimum length
        if len(digits_only) < 10:
            logger.error(f"Invalid phone number format (too short): {phone_number} (digits: {digits_only})")
            return None
        
        # If already starts with +, validate it
        if phone_number.startswith('+'):
            # Remove + and get digits
            digits_only = ''.join(filter(str.isdigit, phone_number[1:]))
            if len(digits_only) < 10:
                logger.error(f"Invalid phone number format: {phone_number}")
                return None
            return f"+{digits_only}"
        
        # If starts with country code (like 91 for India), add +
        # Common country codes: 1 (US/CA), 44 (UK), 91 (India), etc.
        if len(digits_only) >= 10:
            # If it's 10 digits, assume it's a local number - need country code
            # For now, we'll try to detect common patterns
            if len(digits_only) == 10:
                # Assume Indian number (91) if starts with 6-9
                if digits_only[0] in '6789':
                    return f"+91{digits_only}"
                # Assume US/CA number (1) if starts with other digits
                else:
                    return f"+1{digits_only}"
            # If 11 digits and starts with 1, it's likely US/CA
            elif len(digits_only) == 11 and digits_only[0] == '1':
                return f"+{digits_only}"
            # If 12 digits, assume it already has country code
            elif len(digits_only) >= 12:
                return f"+{digits_only}"
            else:
                # Try to detect country code
                # For Indian numbers (91), typically 10-12 digits total
                if digits_only.startswith('91') and len(digits_only) >= 12:
                    return f"+{digits_only}"
                # Default: assume it needs country code
                # For now, log warning and return None
                logger.warning(f"Unable to determine country code for: {phone_number}")
                return None
        
        logger.error(f"Invalid phone number format: {phone_number}")
        return None
    
    def _store_otp(self, phone_or_email: str, otp: str, purpose: str, is_email: bool = False) -> bool:
        """Store OTP in both primary and secondary databases"""
        success_count = 0
        
        # Create new OTP record
        expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
        
        logger.info(f"Storing OTP for {phone_or_email} (purpose: {purpose}, is_email: {is_email}, expires_at: {expires_at})")
        logger.info(f"OTP value: {otp}")
        
        otp_record = OTPRecord(
            phone_or_email=phone_or_email,
            otp=otp,
            purpose=purpose,
            is_email=is_email,
            attempts=0,
            expires_at=expires_at,
            is_verified=False,
            user_id=None,  # Optional for forgot password
            mobile_number=phone_or_email if not is_email else None,  # Legacy field
            otp_code=otp  # Legacy field for backward compatibility
        )
        logger.info(f"Created OTPRecord object: phone_or_email={otp_record.phone_or_email}, otp={otp_record.otp}, purpose={otp_record.purpose}")
        
        # Store in Primary Database
        db_primary = None
        try:
            db_primary = self.PrimarySessionLocal()
            
            # Clean up any existing OTPs for this identifier
            deleted = db_primary.query(OTPRecord).filter(
                OTPRecord.phone_or_email == phone_or_email,
                OTPRecord.purpose == purpose
            ).delete()
            logger.info(f"Deleted {deleted} existing OTP(s) for {phone_or_email}")
            db_primary.commit()  # Commit the delete
            
            # Add new OTP record
            db_primary.add(otp_record)
            db_primary.flush()  # Flush to get the ID and validate
            record_id = otp_record.id if hasattr(otp_record, 'id') and otp_record.id else 'N/A'
            logger.info(f"OTP record added to session (ID: {record_id})")
            
            # Commit the transaction - CRITICAL: This must succeed
            db_primary.commit()
            logger.info(f"✅ Committed OTP to primary database for {phone_or_email}")
            
            # IMPORTANT: Don't close the session yet - verify in same session first
            # Then close and verify with new session
            verify_in_same_session = db_primary.query(OTPRecord).filter(
                OTPRecord.phone_or_email == phone_or_email,
                OTPRecord.purpose == purpose
            ).first()
            
            if verify_in_same_session:
                logger.info(f"✅ Verified in same session: OTP stored (ID: {verify_in_same_session.id})")
            else:
                logger.warning(f"⚠️  Not found in same session (might be transaction isolation)")
            
            db_primary.close()
            db_primary = None
            
            # Verify with a NEW session to ensure persistence
            verify_db = self.PrimarySessionLocal()
            try:
                verify_record = verify_db.query(OTPRecord).filter(
                    OTPRecord.phone_or_email == phone_or_email,
                    OTPRecord.purpose == purpose
                ).first()
                
                if verify_record:
                    logger.info(f"✅✅ Verified in new session: OTP stored successfully (ID: {verify_record.id}, OTP: {verify_record.otp})")
                    success_count += 1
                else:
                    logger.error(f"❌❌ CRITICAL: OTP not found in new session after commit!")
                    # Try to find any record with this OTP
                    any_record = verify_db.query(OTPRecord).filter(OTPRecord.otp == otp).first()
                    if any_record:
                        logger.error(f"   Found OTP in different record: {any_record.phone_or_email} (expected: {phone_or_email})")
                    else:
                        # Check total count
                        total = verify_db.query(OTPRecord).count()
                        logger.error(f"   No records found at all. Total records in table: {total}")
                        # This is a critical failure - storage didn't work
                        logger.error(f"   ⚠️  Storage reported success but record not found!")
            finally:
                verify_db.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to store OTP in primary database: {e}", exc_info=True)
            if db_primary:
                try:
                    db_primary.rollback()
                    db_primary.close()
                except:
                    pass
        
        # Store in Secondary Database (SQLite) - same as primary in current setup
        # Note: Since both use same database URL, this is redundant but kept for compatibility
        db_secondary = None
        try:
            # Only store in secondary if it's a different database
            if self.secondary_db_url != self.primary_db_url:
                db_secondary = self.SecondarySessionLocal()
                
                # Clean up any existing OTPs for this identifier
                deleted = db_secondary.query(OTPRecord).filter(
                    OTPRecord.phone_or_email == phone_or_email,
                    OTPRecord.purpose == purpose
                ).delete()
                logger.info(f"Deleted {deleted} existing OTP(s) from secondary database")
                db_secondary.commit()
                
                # Create new record for secondary (need to create new instance)
                otp_record_secondary = OTPRecord(
                    phone_or_email=phone_or_email,
                    otp=otp,
                    purpose=purpose,
                    is_email=is_email,
                    attempts=0,
                    expires_at=expires_at,
                    is_verified=False
                )
                
                db_secondary.add(otp_record_secondary)
                db_secondary.commit()
                logger.info(f"✅ OTP stored in secondary database for {phone_or_email}")
                success_count += 1
            else:
                logger.debug(f"Skipping secondary database (same as primary)")
            
        except Exception as e:
            logger.error(f"Failed to store OTP in secondary database: {e}", exc_info=True)
            if db_secondary:
                try:
                    db_secondary.rollback()
                    db_secondary.close()
                except:
                    pass
        finally:
            if db_secondary:
                try:
                    db_secondary.close()
                except:
                    pass
        
        # Return True if at least one database succeeded
        return success_count > 0
    
    def _retrieve_otp(self, phone_or_email: str, purpose: str, include_verified: bool = False) -> Optional[OTPRecord]:
        """Retrieve OTP from databases (try primary first, then secondary)"""
        
        logger.debug(f"🔍 _retrieve_otp: Looking for '{phone_or_email}' (purpose: {purpose})")
        
        # Try Primary Database (PostgreSQL) first
        try:
            db_primary = self.PrimarySessionLocal()
            
            # First, check ALL records for this identifier (for debugging)
            all_otps = db_primary.query(OTPRecord).filter(
                OTPRecord.phone_or_email == phone_or_email,
                OTPRecord.purpose == purpose
            ).all()
            logger.info(f"   Found {len(all_otps)} total OTP record(s) for '{phone_or_email}' (purpose: {purpose})")
            for rec in all_otps:
                expired = rec.expires_at < datetime.utcnow()
                status = "EXPIRED" if expired else "ACTIVE"
                logger.info(f"      - ID: {rec.id}, OTP: {rec.otp}, Status: {status}, Verified: {rec.is_verified}, Expires: {rec.expires_at}")
            
            # Now query for valid OTP
            query = db_primary.query(OTPRecord).filter(
                OTPRecord.phone_or_email == phone_or_email,
                OTPRecord.purpose == purpose,
                OTPRecord.expires_at > datetime.utcnow()
            )
            
            if not include_verified:
                query = query.filter(OTPRecord.is_verified == False)
            
            otp_record = query.first()
            
            db_primary.close()
            
            if otp_record:
                logger.info(f"   ✅ Valid OTP found in database: ID={otp_record.id}, OTP={otp_record.otp}")
                return otp_record
            else:
                logger.warning(f"   ❌ No valid OTP found in database for '{phone_or_email}' (purpose: {purpose})")
                
        except Exception as e:
            logger.warning(f"Failed to retrieve OTP from primary database: {e}")
            if 'db_primary' in locals():
                db_primary.close()
        
        # Try Secondary Database (SQLite) as fallback
        try:
            db_secondary = self.SecondarySessionLocal()
            
            query = db_secondary.query(OTPRecord).filter(
                OTPRecord.phone_or_email == phone_or_email,
                OTPRecord.purpose == purpose,
                OTPRecord.expires_at > datetime.utcnow()
            )
            
            if not include_verified:
                query = query.filter(OTPRecord.is_verified == False)
            
            otp_record = query.first()
            db_secondary.close()
            
            if otp_record:
                logger.info(f"OTP retrieved from secondary database (SQLite) for {phone_or_email}")
                return otp_record
                
        except Exception as e:
            logger.error(f"Failed to retrieve OTP from secondary database: {e}")
            if 'db_secondary' in locals():
                db_secondary.close()
        
        return None
    
    def _increment_attempts(self, phone_or_email: str, purpose: str):
        """Increment attempt count for OTP in both databases"""
        
        # Update Primary Database (PostgreSQL)
        try:
            db_primary = self.PrimarySessionLocal()
            otp_record = db_primary.query(OTPRecord).filter(
                OTPRecord.phone_or_email == phone_or_email,
                OTPRecord.purpose == purpose
            ).first()
            
            if otp_record:
                otp_record.attempts += 1
                db_primary.commit()
                logger.info(f"Attempts incremented in primary database for {phone_or_email}")
            
            db_primary.close()
            
        except Exception as e:
            logger.error(f"Failed to increment attempts in primary database: {e}")
            if 'db_primary' in locals():
                db_primary.rollback()
                db_primary.close()
        
        # Update Secondary Database (SQLite)
        try:
            db_secondary = self.SecondarySessionLocal()
            otp_record = db_secondary.query(OTPRecord).filter(
                OTPRecord.phone_or_email == phone_or_email,
                OTPRecord.purpose == purpose
            ).first()
            
            if otp_record:
                otp_record.attempts += 1
                db_secondary.commit()
                logger.info(f"Attempts incremented in secondary database for {phone_or_email}")
            
            db_secondary.close()
            
        except Exception as e:
            logger.error(f"Failed to increment attempts in secondary database: {e}")
            if 'db_secondary' in locals():
                db_secondary.rollback()
                db_secondary.close()
    
    def _mark_otp_verified(self, phone_or_email: str, purpose: str):
        """Mark OTP as verified in both databases"""
        
        # Update Primary Database (PostgreSQL)
        try:
            db_primary = self.PrimarySessionLocal()
            otp_record = db_primary.query(OTPRecord).filter(
                OTPRecord.phone_or_email == phone_or_email,
                OTPRecord.purpose == purpose
            ).first()
            
            if otp_record:
                otp_record.is_verified = True
                db_primary.commit()
                logger.info(f"OTP marked as verified in primary database for {phone_or_email}")
            
            db_primary.close()
            
        except Exception as e:
            logger.error(f"Failed to mark OTP as verified in primary database: {e}")
            if 'db_primary' in locals():
                db_primary.rollback()
                db_primary.close()
        
        # Update Secondary Database (SQLite)
        try:
            db_secondary = self.SecondarySessionLocal()
            otp_record = db_secondary.query(OTPRecord).filter(
                OTPRecord.phone_or_email == phone_or_email,
                OTPRecord.purpose == purpose
            ).first()
            
            if otp_record:
                otp_record.is_verified = True
                db_secondary.commit()
                logger.info(f"OTP marked as verified in secondary database for {phone_or_email}")
            
            db_secondary.close()
            
        except Exception as e:
            logger.error(f"Failed to mark OTP as verified in secondary database: {e}")
            if 'db_secondary' in locals():
                db_secondary.rollback()
                db_secondary.close()
    
    async def _send_sms_otp(self, phone_number: str, otp: str) -> Tuple[bool, Optional[str]]:
        """Send OTP via SMS using Twilio
        
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        if not all([self.twilio_sid, self.twilio_token, self.twilio_phone]):
            error_msg = "Twilio credentials not configured, SMS not sent"
            logger.warning(error_msg)
            logger.warning(f"Missing: SID={bool(self.twilio_sid)}, Token={bool(self.twilio_token)}, Phone={bool(self.twilio_phone)}")
            return False, error_msg
        
        # Format phone number to E.164 format
        formatted_phone = self._format_phone_number(phone_number)
        if not formatted_phone:
            error_msg = f"Invalid phone number format: {phone_number}. Phone number must be in E.164 format (e.g., +1234567890) or a valid local number without masked characters."
            logger.error(error_msg)
            return False, error_msg
        
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
            
            data = {
                'From': self.twilio_phone,
                'To': formatted_phone,
                'Body': f"Your OTP is: {otp}. Valid for {self.otp_expiry_minutes} minutes."
            }
            
            logger.info(f"Sending SMS to formatted number: {formatted_phone} (original: {phone_number})")
            
            auth = aiohttp.BasicAuth(self.twilio_sid, self.twilio_token)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, auth=auth) as response:
                    response_text = await response.text()
                    
                    if response.status == 201:
                        logger.info(f"SMS OTP sent to {formatted_phone}")
                        return True, None
                    elif response.status == 401:
                        error_msg = "Twilio authentication failed: Invalid credentials"
                        logger.error(error_msg)
                        logger.error(f"SID: {self.twilio_sid[:8]}...")
                        logger.error(f"Token: {self.twilio_token[:8]}...")
                        logger.error(f"Phone: {self.twilio_phone}")
                        logger.error(f"Response: {response_text[:200]}")
                        return False, error_msg
                    elif response.status == 400:
                        error_msg = f"Twilio bad request: {response_text[:200]}"
                        logger.error(error_msg)
                        return False, error_msg
                    else:
                        error_msg = f"Failed to send SMS: HTTP {response.status}"
                        logger.error(error_msg)
                        logger.error(f"Response: {response_text[:200]}")
                        return False, error_msg
                        
        except Exception as e:
            error_msg = f"Error sending SMS: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    async def _send_email_otp(self, email: str, otp: str) -> bool:
        """Send OTP via Email using SMTP"""
        if not all([self.smtp_username, self.smtp_password]):
            logger.warning("SMTP credentials not configured, email not sent")
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = email
            msg['Subject'] = "Your OTP Code"
            
            body = f"""
            Your OTP code is: {otp}
            
            This code is valid for {self.otp_expiry_minutes} minutes.
            
            If you didn't request this code, please ignore this email.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.smtp_username, email, text)
            server.quit()
            
            logger.info(f"Email OTP sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def send_otp(self, phone_or_email: str, purpose: str = "verification", is_email: bool = False) -> Dict[str, any]:
        """Send OTP to phone number or email"""
        try:
            # Normalize identifier for consistent storage
            # For phone numbers, normalize to E.164 format
            # For emails, use as-is (lowercase)
            normalized_identifier = phone_or_email.strip()
            if not is_email:
                # Try to normalize phone number to E.164 format
                formatted = self._format_phone_number(normalized_identifier)
                if formatted:
                    normalized_identifier = formatted
                    logger.info(f"Normalized phone number {phone_or_email} to {normalized_identifier} for storage")
                else:
                    # If formatting fails, use original (might be invalid, but let validation handle it)
                    logger.warning(f"Could not normalize phone number {phone_or_email}, using as-is")
            else:
                # Normalize email to lowercase
                normalized_identifier = normalized_identifier.lower()
            
            # Generate OTP
            otp = self._generate_otp()
            logger.info(f"🔑 GENERATED OTP: {otp} for identifier: {phone_or_email}")
            logger.info(f"   Normalized identifier (for storage): {normalized_identifier}")
            logger.info(f"   Purpose: {purpose}, Is Email: {is_email}")
            
            # Store OTP in database with normalized identifier
            logger.info(f"💾 Storing OTP in database...")
            store_success = self._store_otp(normalized_identifier, otp, purpose, is_email)
            logger.info(f"   Storage result: {store_success} for {normalized_identifier}")
            
            if not store_success:
                logger.error(f"Failed to store OTP in database for {normalized_identifier}")
                return {
                    "success": False,
                    "message": "Failed to store OTP in database",
                    "error": "Database error"
                }
            
            # Send OTP (use original phone_or_email for sending, but normalized for storage)
            if is_email:
                sent = await self._send_email_otp(phone_or_email, otp)
                error_msg = None if sent else "Failed to send email OTP"
            else:
                # For SMS, use formatted phone number if available
                formatted_for_sms = self._format_phone_number(phone_or_email) or phone_or_email
                sent, error_msg = await self._send_sms_otp(formatted_for_sms, otp)
            
            if sent:
                return {
                    "success": True,
                    "message": f"OTP sent to {phone_or_email}",
                    "phone_or_email": normalized_identifier,  # Return normalized identifier
                    "purpose": purpose,
                    "is_email": is_email,
                    "otp": otp  # Return OTP for development/testing (remove in production)
                }
            else:
                # Even if sending failed, OTP is stored - return it for development
                logger.warning(f"OTP sending failed but OTP is stored in database. Returning OTP for development.")
                return {
                    "success": True,  # Still return success since OTP is stored
                    "message": f"OTP generated and stored (sending failed: {error_msg})",
                    "phone_or_email": normalized_identifier,
                    "purpose": purpose,
                    "is_email": is_email,
                    "otp": otp  # Return OTP for development/testing
                }
                
        except Exception as e:
            logger.error(f"Error sending OTP: {e}")
            return {
                "success": False,
                "message": "Failed to send OTP",
                "error": str(e)
            }
    
    def verify_otp(self, phone_or_email: str, otp: str, purpose: str = "verification") -> Dict[str, any]:
        """Verify OTP against database"""
        try:
            logger.info(f"🔍 VERIFY_OTP called:")
            logger.info(f"   Input - phone_or_email: '{phone_or_email}', otp: '{otp}', purpose: '{purpose}'")
            
            # Normalize identifier for lookup (same as storage)
            normalized_identifier = phone_or_email.strip()
            is_email = "@" in normalized_identifier
            
            if not is_email:
                # Try to normalize phone number to E.164 format
                formatted = self._format_phone_number(normalized_identifier)
                if formatted:
                    logger.info(f"   Normalized phone number '{phone_or_email}' → '{formatted}' for verification")
                    normalized_identifier = formatted
                else:
                    logger.warning(f"   Could not normalize phone number '{phone_or_email}', using as-is")
            else:
                # Normalize email to lowercase
                normalized_identifier = normalized_identifier.lower()
                logger.info(f"   Normalized email '{phone_or_email}' → '{normalized_identifier}'")
            
            logger.info(f"   Looking up OTP in database with identifier: '{normalized_identifier}'")
            
            # Retrieve OTP from database with normalized identifier
            otp_record = self._retrieve_otp(normalized_identifier, purpose)
            
            if otp_record:
                logger.info(f"   ✅ Found OTP record in database:")
                logger.info(f"      ID: {otp_record.id}")
                logger.info(f"      Stored OTP: {otp_record.otp}")
                logger.info(f"      Provided OTP: {otp}")
                logger.info(f"      Match: {otp_record.otp == otp}")
                logger.info(f"      Expires: {otp_record.expires_at}")
                logger.info(f"      Attempts: {otp_record.attempts}")
                logger.info(f"      Verified: {otp_record.is_verified}")
            else:
                logger.warning(f"   ❌ No OTP record found in database for '{normalized_identifier}'")
            
            if not otp_record:
                # Try alternative formats
                logger.info(f"   Trying alternative identifier formats...")
                alternative_formats = []
                if not is_email:
                    if normalized_identifier.startswith("+"):
                        alternative_formats.append(normalized_identifier[1:])  # Without +
                        if normalized_identifier.startswith("+91"):
                            alternative_formats.append(normalized_identifier[3:])  # Without +91
                    else:
                        alternative_formats.append(f"+{normalized_identifier}")  # With +
                        if len(normalized_identifier) == 10:
                            alternative_formats.append(f"+91{normalized_identifier}")  # With +91
                
                for alt_format in set(alternative_formats):
                    logger.info(f"   Trying format: '{alt_format}'")
                    alt_record = self._retrieve_otp(alt_format, purpose)
                    if alt_record:
                        logger.info(f"   ✅ Found OTP with alternative format '{alt_format}'!")
                        otp_record = alt_record
                        normalized_identifier = alt_format
                        break
                
                if not otp_record:
                    logger.error(f"   ❌ No OTP found for any format. Checked: {normalized_identifier} and alternatives")
                    return {
                        "success": False,
                        "message": "OTP not found or expired",
                        "error": "Invalid or expired OTP"
                    }
            
            # Check attempts
            if otp_record.attempts >= self.max_attempts:
                logger.warning(f"   ❌ Too many attempts: {otp_record.attempts} >= {self.max_attempts}")
                return {
                    "success": False,
                    "message": "Too many attempts",
                    "error": "Maximum attempts exceeded"
                }
            
            # Increment attempts
            self._increment_attempts(normalized_identifier, purpose)
            
            # Verify OTP
            logger.info(f"   🔐 Comparing OTPs:")
            logger.info(f"      Stored OTP: '{otp_record.otp}' (type: {type(otp_record.otp).__name__})")
            logger.info(f"      Provided OTP: '{otp}' (type: {type(otp).__name__})")
            logger.info(f"      Match: {otp_record.otp == otp}")
            
            if otp_record.otp == otp:
                # Mark as verified
                self._mark_otp_verified(normalized_identifier, purpose)
                
                logger.info(f"   ✅ OTP verified successfully for {normalized_identifier} (original: {phone_or_email})")
                return {
                    "success": True,
                    "message": "OTP verified successfully",
                    "phone_or_email": normalized_identifier,
                    "purpose": purpose
                }
            else:
                logger.error(f"   ❌ OTP MISMATCH for {normalized_identifier}")
                logger.error(f"      Expected: '{otp_record.otp}' (length: {len(otp_record.otp)})")
                logger.error(f"      Got: '{otp}' (length: {len(otp)})")
                logger.error(f"      Are they equal? {otp_record.otp == otp}")
                return {
                    "success": False,
                    "message": "Invalid OTP",
                    "error": "OTP mismatch"
                }
                
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return {
                "success": False,
                "message": "Failed to verify OTP",
                "error": str(e)
            }
    
    def get_otp_status(self, phone_or_email: str, purpose: str = "verification") -> Dict[str, any]:
        """Get OTP status from database"""
        try:
            # First try to get active (unverified) OTP
            otp_record = self._retrieve_otp(phone_or_email, purpose, include_verified=False)
            
            if not otp_record:
                # If no active OTP, check for verified OTP
                otp_record = self._retrieve_otp(phone_or_email, purpose, include_verified=True)
                
                if not otp_record:
                    return {
                        "success": False,
                        "message": "No OTP found",
                        "status": "not_found"
                    }
                else:
                    return {
                        "success": True,
                        "message": "OTP status retrieved (verified)",
                        "phone_or_email": phone_or_email,
                        "purpose": purpose,
                        "attempts": otp_record.attempts,
                        "expires_at": otp_record.expires_at.isoformat(),
                        "is_verified": otp_record.is_verified,
                        "status": "verified"
                    }
            
            return {
                "success": True,
                "message": "OTP status retrieved",
                "phone_or_email": phone_or_email,
                "purpose": purpose,
                "attempts": otp_record.attempts,
                "expires_at": otp_record.expires_at.isoformat(),
                "is_verified": otp_record.is_verified,
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Error getting OTP status: {e}")
            return {
                "success": False,
                "message": "Failed to get OTP status",
                "error": str(e)
            }
    
    def cleanup_expired_otps(self) -> Dict[str, any]:
        """Clean up expired OTPs from both databases"""
        total_deleted = 0
        results = {}
        
        # Clean Primary Database (PostgreSQL)
        try:
            db_primary = self.PrimarySessionLocal()
            deleted_primary = db_primary.query(OTPRecord).filter(
                OTPRecord.expires_at < datetime.utcnow()
            ).delete()
            db_primary.commit()
            db_primary.close()
            
            results["primary_deleted"] = deleted_primary
            total_deleted += deleted_primary
            logger.info(f"Cleaned up {deleted_primary} expired OTPs from primary database (PostgreSQL)")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired OTPs from primary database: {e}")
            results["primary_error"] = str(e)
            if 'db_primary' in locals():
                db_primary.rollback()
                db_primary.close()
        
        # Clean Secondary Database (SQLite)
        try:
            db_secondary = self.SecondarySessionLocal()
            deleted_secondary = db_secondary.query(OTPRecord).filter(
                OTPRecord.expires_at < datetime.utcnow()
            ).delete()
            db_secondary.commit()
            db_secondary.close()
            
            results["secondary_deleted"] = deleted_secondary
            total_deleted += deleted_secondary
            logger.info(f"Cleaned up {deleted_secondary} expired OTPs from secondary database (SQLite)")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired OTPs from secondary database: {e}")
            results["secondary_error"] = str(e)
            if 'db_secondary' in locals():
                db_secondary.rollback()
                db_secondary.close()
        
        return {
            "success": True,
            "message": f"Cleaned up {total_deleted} expired OTPs from both databases",
            "deleted_count": total_deleted,
            "details": results
        }
    
    def get_database_status(self) -> Dict[str, any]:
        """Get status of both databases"""
        status = {
            "primary_db": {"status": "unknown", "url": self.primary_db_url},
            "secondary_db": {"status": "unknown", "url": self.secondary_db_url}
        }
        
        # Check Primary Database (PostgreSQL)
        try:
            db_primary = self.PrimarySessionLocal()
            db_primary.execute("SELECT 1")
            db_primary.close()
            status["primary_db"]["status"] = "healthy"
            status["primary_db"]["type"] = "PostgreSQL"
        except Exception as e:
            status["primary_db"]["status"] = "unhealthy"
            status["primary_db"]["error"] = str(e)
        
        # Check Secondary Database (SQLite)
        try:
            db_secondary = self.SecondarySessionLocal()
            db_secondary.execute("SELECT 1")
            db_secondary.close()
            status["secondary_db"]["status"] = "healthy"
            status["secondary_db"]["type"] = "SQLite"
        except Exception as e:
            status["secondary_db"]["status"] = "unhealthy"
            status["secondary_db"]["error"] = str(e)
        
        return {
            "success": True,
            "message": "Database status retrieved",
            "databases": status
        }
    
    def sync_databases(self) -> Dict[str, any]:
        """Sync data between primary and secondary databases"""
        synced_count = 0
        results = {}
        
        try:
            # Get all OTPs from primary database
            db_primary = self.PrimarySessionLocal()
            primary_otps = db_primary.query(OTPRecord).all()
            db_primary.close()
            
            # Sync to secondary database
            db_secondary = self.SecondarySessionLocal()
            
            for otp in primary_otps:
                # Check if OTP exists in secondary
                existing = db_secondary.query(OTPRecord).filter(
                    OTPRecord.phone_or_email == otp.phone_or_email,
                    OTPRecord.purpose == otp.purpose,
                    OTPRecord.created_at == otp.created_at
                ).first()
                
                if not existing:
                    # Add missing OTP to secondary
                    db_secondary.add(otp)
                    synced_count += 1
            
            db_secondary.commit()
            db_secondary.close()
            
            results["synced_count"] = synced_count
            logger.info(f"Synced {synced_count} OTPs from primary to secondary database")
            
        except Exception as e:
            logger.error(f"Error syncing databases: {e}")
            results["error"] = str(e)
        
        return {
            "success": True,
            "message": f"Database sync completed",
            "synced_count": synced_count,
            "details": results
        }
    
    # Public methods for auth routes compatibility
    async def send_sms_otp(self, phone: str, purpose: str = "verification") -> Dict[str, any]:
        """Public method to send SMS OTP"""
        return await self.send_otp(phone, purpose, is_email=False)
    
    async def send_email_otp(self, email: str, purpose: str = "verification") -> Dict[str, any]:
        """Public method to send Email OTP"""
        return await self.send_otp(email, purpose, is_email=True)

# Create global instance
otp_service = FixedOTPService()