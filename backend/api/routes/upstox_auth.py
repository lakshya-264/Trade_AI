"""
Upstox OAuth Authentication Routes
Handles Upstox API authentication and token management
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse, JSONResponse
import os
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

# Upstox credentials from environment
API_KEY = os.getenv("UPSTOX_API_KEY")
API_SECRET = os.getenv("UPSTOX_API_SECRET")
REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI", "http://localhost:3000/callback")

@router.get("/login")
async def upstox_login():
    """
    Initiate Upstox OAuth flow
    
    Returns authorization URL that user needs to visit
    """
    try:
        if not API_KEY:
            raise HTTPException(
                status_code=500,
                detail="Upstox API key not configured. Set UPSTOX_API_KEY in .env"
            )
        
        # Import upstox client
        try:
            from upstox_client import Configuration, ApiClient, LoginApi
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="upstox-client not installed. Run: pip install upstox-client"
            )
        
        configuration = Configuration()
        configuration.api_key['APIKEY'] = API_KEY
        
        api_client = ApiClient(configuration)
        login_api = LoginApi(api_client)
        
        # Generate authorization URL
        auth_url = login_api.authorize(API_KEY, REDIRECT_URI)
        
        logger.info(f"✅ Generated Upstox auth URL")
        
        return {
            "success": True,
            "authorization_url": auth_url,
            "redirect_uri": REDIRECT_URI,
            "instructions": [
                "1. Open the authorization_url in your browser",
                "2. Login to your Upstox account",
                "3. Authorize the application",
                "4. You will be redirected back with an authorization code",
                "5. Use the code with /api/upstox/callback endpoint"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating Upstox auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback")
async def upstox_callback(code: str = Query(..., description="Authorization code from Upstox")):
    """
    Handle Upstox OAuth callback
    
    Exchange authorization code for access token
    """
    try:
        if not API_KEY or not API_SECRET:
            raise HTTPException(
                status_code=500,
                detail="Upstox credentials not configured"
            )
        
        # Import upstox client
        try:
            from upstox_client import Configuration, ApiClient
            from upstox_client.api.login_api import LoginApi
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="upstox-client not installed"
            )
        
        configuration = Configuration()
        api_client = ApiClient(configuration)
        login_api = LoginApi(api_client)
        
        # Exchange code for access token
        try:
            token_response = login_api.token(
                api_version="2.0",
                code=code,
                client_id=API_KEY,
                client_secret=API_SECRET,
                redirect_uri=REDIRECT_URI,
                grant_type="authorization_code"
            )
        except Exception as token_error:
            logger.error(f"❌ Token exchange failed: {token_error}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange code for token: {token_error}"
            )
        
        # Extract tokens
        access_token = token_response.access_token
        
        # Update environment variables (in production, save to secure storage/database)
        os.environ["UPSTOX_ACCESS_TOKEN"] = access_token
        
        # Reinitialize Upstox service with new token
        from core.upstox_service import upstox_service
        upstox_service.access_token = access_token
        upstox_service.quote_api = None  # Force re-initialization
        
        logger.info("✅ Upstox authentication successful!")
        
        return {
            "success": True,
            "message": "Upstox authentication successful",
            "access_token": access_token[:10] + "..." + access_token[-10:],  # Partial token for security
            "timestamp": datetime.now().isoformat(),
            "next_steps": [
                "Access token has been saved to environment",
                "Upstox service is now active",
                "Test it with: GET /api/upstox/status"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh")
async def refresh_access_token():
    """
    Refresh Upstox access token (if available)
    
    Note: Upstox API v2 tokens are typically long-lived
    Check Upstox documentation for token refresh requirements
    """
    try:
        logger.warning("⚠️  Token refresh not implemented - Upstox API v2 tokens are long-lived")
        
        return {
            "success": False,
            "message": "Token refresh not required for Upstox API v2",
            "note": "Upstox API v2 tokens are long-lived. Re-authenticate if token expires."
        }
        
    except Exception as e:
        logger.error(f"❌ Error refreshing token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def upstox_status():
    """
    Get Upstox service status and health
    """
    try:
        from core.upstox_service import upstox_service
        
        health_status = upstox_service.get_health_status()
        
        return {
            "success": True,
            "upstox_configured": bool(API_KEY and os.getenv("UPSTOX_ACCESS_TOKEN")),
            "api_key_set": bool(API_KEY),
            "access_token_set": bool(os.getenv("UPSTOX_ACCESS_TOKEN")),
            "health_status": health_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting Upstox status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-quote")
async def test_upstox_quote(symbol: str = Query("RELIANCE", description="Stock symbol to test")):
    """
    Test Upstox API with a sample quote
    """
    try:
        from core.upstox_service import upstox_service
        
        if not upstox_service.is_healthy():
            raise HTTPException(
                status_code=503,
                detail="Upstox service not healthy. Check configuration and authentication."
            )
        
        # Get quote
        quote = await upstox_service.get_quote(symbol, "NSE")
        
        if "error" in quote:
            return {
                "success": False,
                "error": quote.get("error"),
                "symbol": symbol
            }
        
        return {
            "success": True,
            "symbol": symbol,
            "quote": quote,
            "message": f"Successfully fetched {symbol} quote from Upstox"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error testing Upstox quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear-cache")
async def clear_upstox_cache():
    """Clear Upstox service cache"""
    try:
        from core.upstox_service import upstox_service
        
        upstox_service.clear_cache()
        
        return {
            "success": True,
            "message": "Upstox cache cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instruments")
async def get_supported_instruments():
    """Get list of supported instruments"""
    try:
        from core.upstox_service import upstox_service
        
        return {
            "success": True,
            "count": len(upstox_service.instrument_map),
            "instruments": list(upstox_service.instrument_map.keys()),
            "note": "Additional symbols may work but are not guaranteed"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

