"""
Angel One SmartAPI integration for live trading
"""

import asyncio
import aiohttp
import json
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AngelOneAPI:
    def __init__(self):
        self.api_key = os.getenv("ANGEL_ONE_API_KEY")
        self.client_id = os.getenv("ANGEL_ONE_CLIENT_ID")
        self.username = os.getenv("ANGEL_ONE_USERNAME") or os.getenv("ANGEL_ONE_CLIENT_ID")
        self.password = os.getenv("ANGEL_ONE_PASSWORD")
        self.pin = os.getenv("ANGEL_ONE_PIN")
        self.totp_secret = os.getenv("ANGEL_ONE_TOTP_SECRET")
        
        self.base_url = "https://smartapi.angelbroking.com"
        self.session = None
        self.access_token = None
        self.refresh_token = None
        self.feed_token = None
        self.jwt_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self) -> bool:
        """Login to Angel One API"""
        try:
            if not all([self.api_key, self.client_id, self.password]):
                logger.error("Angel One credentials not configured")
                return False
            
            # Generate TOTP
            totp = self._generate_totp()
            
            # Login request
            login_data = {
                "clientcode": self.client_id,
                "password": self.password,
                "totp": totp
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key
            }
            
            url = f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword"
            
            async with self.session.post(url, json=login_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status"):
                        self.access_token = data["data"]["jwtToken"]
                        self.refresh_token = data["data"]["refreshToken"]
                        self.feed_token = data["data"]["feedToken"]
                        logger.info("Angel One login successful")
                        return True
                    else:
                        logger.error(f"Angel One login failed: {data.get('message')}")
                        return False
                else:
                    logger.error(f"Angel One login failed with status: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error logging into Angel One: {e}")
            return False
    
    async def get_profile(self) -> Optional[Dict]:
        """Get user profile"""
        try:
            if not self.access_token:
                await self.login()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key
            }
            
            url = f"{self.base_url}/rest/secure/angelbroking/user/v1/getProfile"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data")
                else:
                    logger.error(f"Error getting profile: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None
    
    async def get_holdings(self) -> Optional[List[Dict]]:
        """Get user holdings"""
        try:
            if not self.access_token:
                await self.login()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key
            }
            
            url = f"{self.base_url}/rest/secure/angelbroking/portfolio/v1/getHolding"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    logger.error(f"Error getting holdings: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting holdings: {e}")
            return None
    
    async def place_order(self, order_data: Dict) -> Optional[Dict]:
        """Place an order"""
        try:
            if not self.access_token:
                await self.login()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key
            }
            
            url = f"{self.base_url}/rest/secure/angelbroking/order/v1/placeOrder"
            
            async with self.session.post(url, json=order_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Error placing order: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    async def get_order_book(self) -> Optional[List[Dict]]:
        """Get order book"""
        try:
            if not self.access_token:
                await self.login()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key
            }
            
            url = f"{self.base_url}/rest/secure/angelbroking/order/v1/getOrderBook"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    logger.error(f"Error getting order book: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting order book: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> Optional[Dict]:
        """Cancel an order"""
        try:
            if not self.access_token:
                await self.login()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key
            }
            
            url = f"{self.base_url}/rest/secure/angelbroking/order/v1/cancelOrder"
            cancel_data = {"variety": "NORMAL", "orderid": order_id}
            
            async with self.session.post(url, json=cancel_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Error canceling order: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            return None
    
    async def get_quote(self, symbol: str, exchange: str = "NSE") -> Optional[Dict]:
        """Get live quote"""
        try:
            if not self.access_token:
                await self.login()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key
            }
            
            url = f"{self.base_url}/rest/secure/angelbroking/market/v1/quote"
            
            # Convert symbol to token if needed (for now, use symbol as token)
            symbol_token = symbol
            if symbol == "RELIANCE":
                symbol_token = "2881"  # RELIANCE token for NSE
            
            quote_data = {
                "mode": "FULL",
                "exchangeTokens": {
                    exchange: [symbol_token]
                }
            }
            
            async with self.session.post(url, json=quote_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") and data.get("data"):
                        # Parse the quote data
                        quote_info = data["data"].get("fetched", [])
                        if quote_info:
                            quote = quote_info[0]
                            return {
                                'symbol': symbol,
                                'lastPrice': float(quote.get('ltp', 0)),
                                'open': float(quote.get('open', 0)),
                                'high': float(quote.get('high', 0)),
                                'low': float(quote.get('low', 0)),
                                'volume': int(quote.get('volume', 0)),
                                'change': float(quote.get('change', 0)),
                                'changePercent': float(quote.get('changePercentage', 0)),
                                'marketCap': 0,  # Not available in quote
                                'pe': 0,  # Not available in quote
                                'pb': 0,  # Not available in quote
                                'eps': 0,  # Not available in quote
                                'source': 'angel_one',
                                'timestamp': datetime.now().isoformat()
                            }
                    return None
                else:
                    logger.error(f"Angel One quote API failed with status: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, exchange: str = "NSE", 
                                 from_date: str = None, to_date: str = None) -> Optional[List[Dict]]:
        """Get historical data"""
        try:
            if not self.access_token:
                await self.login()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key
            }
            
            # Set default date range if not provided
            if not from_date:
                from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not to_date:
                to_date = datetime.now().strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/rest/secure/angelbroking/market/v1/history"
            historical_data = {
                "mode": "FULL",
                "exchangeTokens": {
                    exchange: [symbol]
                },
                "fromdate": from_date,
                "todate": to_date
            }
            
            async with self.session.post(url, json=historical_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") and data.get("data"):
                        # Parse historical data
                        historical_info = data["data"].get("fetched", [])
                        if historical_info:
                            result = []
                            for item in historical_info:
                                result.append({
                                    'date': item.get('date', ''),
                                    'open': float(item.get('open', 0)),
                                    'high': float(item.get('high', 0)),
                                    'low': float(item.get('low', 0)),
                                    'close': float(item.get('close', 0)),
                                    'volume': int(item.get('volume', 0)),
                                    'source': 'angel_one'
                                })
                            return result
                    return []
                else:
                    logger.error(f"Angel One historical API failed with status: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []
    
    async def get_market_status(self) -> Optional[Dict]:
        """Get market status"""
        try:
            if not self.access_token:
                await self.login()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key
            }
            
            url = f"{self.base_url}/rest/secure/angelbroking/market/v1/marketStatus"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") and data.get("data"):
                        market_data = data["data"]
                        return {
                            'market_status': 'OPEN' if market_data.get('marketStatus') == 'Open' else 'CLOSED',
                            'market_hours': '09:00 - 15:30',
                            'current_time': datetime.now().strftime('%H:%M:%S'),
                            'next_open': '09:00' if market_data.get('marketStatus') != 'Open' else None,
                            'source': 'angel_one'
                        }
                    return None
                else:
                    logger.error(f"Angel One market status API failed with status: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return None
    
    def _generate_totp(self) -> str:
        """Generate TOTP for authentication"""
        try:
            import pyotp
            totp = pyotp.TOTP(self.totp_secret)
            return totp.now()
        except ImportError:
            logger.error("pyotp not installed. Install with: pip install pyotp")
            return "123456"  # Fallback for testing
        except Exception as e:
            logger.error(f"Error generating TOTP: {e}")
            return "123456"
    
    def _create_order_data(self, symbol: str, order_type: str, quantity: int, 
                          price: float, product: str = "CNC", 
                          variety: str = "NORMAL") -> Dict:
        """Create order data structure"""
        return {
            "variety": variety,
            "tradingsymbol": symbol,
            "symboltoken": "",  # Will be filled by API
            "transactiontype": order_type,
            "exchange": "NSE",
            "ordertype": "MARKET",
            "producttype": product,
            "duration": "DAY",
            "price": str(price),
            "squareoff": "0",
            "stoploss": "0",
            "quantity": str(quantity)
        }
