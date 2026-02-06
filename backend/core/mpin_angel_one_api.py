
"""
Angel One SmartAPI Integration with MPIN Authentication
Using the official smartapi-python library with MPIN
"""

import os
import asyncio
import aiohttp
import json
import pyotp
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dotenv import load_dotenv

# Import the official SmartAPI library
from SmartApi import SmartConnect
from logzero import logger

load_dotenv()

class MPINAngelOneAPI:
    def __init__(self):
        self.api_key = os.getenv("ANGEL_ONE_API_KEY")
        self.client_id = os.getenv("ANGEL_ONE_CLIENT_ID")
        self.username = os.getenv("ANGEL_ONE_USERNAME") or os.getenv("ANGEL_ONE_CLIENT_ID")
        self.mpin = os.getenv("ANGEL_ONE_MPIN") or os.getenv("ANGEL_ONE_PIN")
        self.totp_secret = os.getenv("ANGEL_ONE_TOTP_SECRET")
        
        self.smart_api = None
        self.auth_token = None
        self.refresh_token = None
        self.feed_token = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.smart_api:
            try:
                self.smart_api.terminateSession(self.client_id)
            except:
                pass
    
    async def login(self) -> bool:
        """Login using MPIN authentication."""
        try:
            if not all([self.api_key, self.username, self.mpin, self.totp_secret]):
                logger.error("Angel One credentials not configured")
                return False
            
            # Initialize SmartConnect
            self.smart_api = SmartConnect(self.api_key)
            
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_secret)
            totp_code = totp.now()
            
            # Try MPIN authentication
            data = self.smart_api.generateSession(self.username, self.mpin, totp_code)
            
            if data['status'] == False:
                # Try alternative MPIN authentication
                if hasattr(self.smart_api, 'generateSessionByMPIN'):
                    data = self.smart_api.generateSessionByMPIN(self.username, self.mpin, totp_code)
                else:
                    # Try with different parameter order
                    data = self.smart_api.generateSession(self.mpin, self.username, totp_code)
                
                if data['status'] == False:
                    logger.error(f"Angel One MPIN login failed: {data}")
                    return False
            
            # Extract tokens
            self.auth_token = data['data']['jwtToken']
            self.refresh_token = data['data']['refreshToken']
            self.feed_token = self.smart_api.getfeedToken()
            
            logger.info("Angel One MPIN login successful")
            return True
            
        except Exception as e:
            logger.error(f"Error logging into Angel One with MPIN: {e}")
            return False
    
    async def get_profile(self) -> Optional[Dict]:
        """Get user profile."""
        try:
            if not self.smart_api or not self.refresh_token:
                await self.login()
            
            profile = self.smart_api.getProfile(self.refresh_token)
            return profile.get('data') if profile.get('status') else None
            
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None
    
    async def get_market_status(self) -> Optional[Dict]:
        """Get market status."""
        try:
            if not self.smart_api:
                await self.login()
            
            market_status = self.smart_api.getMarketStatus()
            return market_status
            
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return None
    
    async def get_quote(self, symbol: str, exchange: str = "NSE") -> Optional[Dict]:
        """Get live quote."""
        try:
            if not self.smart_api:
                await self.login()
            
            # Convert symbol to token (simplified mapping)
            symbol_tokens = {
                "RELIANCE": "2881",
                "SBIN": "3045",
                "TCS": "2955"
            }
            
            symbol_token = symbol_tokens.get(symbol, symbol)
            
            quote_params = {
                "exchange": exchange,
                "symboltoken": symbol_token
            }
            
            quote = self.smart_api.getQuote(quote_params)
            return quote
            
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            return None
    
    async def get_holdings(self) -> Optional[List[Dict]]:
        """Get user holdings."""
        try:
            if not self.smart_api:
                await self.login()
            
            holdings = self.smart_api.getHoldings()
            return holdings.get('data', []) if holdings.get('status') else []
            
        except Exception as e:
            logger.error(f"Error getting holdings: {e}")
            return []
    
    async def place_order(self, order_data: Dict) -> Optional[Dict]:
        """Place an order."""
        try:
            if not self.smart_api:
                await self.login()
            
            order_id = self.smart_api.placeOrder(order_data)
            return {"order_id": order_id}
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    async def get_order_book(self) -> Optional[List[Dict]]:
        """Get order book."""
        try:
            if not self.smart_api:
                await self.login()
            
            order_book = self.smart_api.getOrderBook()
            return order_book.get('data', []) if order_book.get('status') else []
            
        except Exception as e:
            logger.error(f"Error getting order book: {e}")
            return []
