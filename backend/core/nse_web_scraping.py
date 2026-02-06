"""
NSE API Service - Using Playwright for Session Management
Based on successful debug session findings
COMMENTED OUT - Using Investing.com scraper instead
"""

# import asyncio
# import logging
# from typing import Dict, Any, Optional
# import aiohttp
# import json
# from datetime import datetime

# logger = logging.getLogger(__name__)

# class NSEWebScrapingService:
#     def __init__(self):
#         self.playwright = None
#         self.browser = None
#         self.page = None
#         self.session = None
#         self.cookies = None
#         self.is_initialized = False
#     
#     async def _ensure_initialized(self):
#         """Ensure we have a valid session using Playwright"""
#         if not self.is_initialized:
#             try:
#                 from playwright.async_api import async_playwright
#                 self.playwright = await async_playwright().start()
#                 
#                 # Launch browser (headless for production)
#                 self.browser = await self.playwright.chromium.launch(
#                     headless=True,
#                     args=[
#                         '--no-sandbox',
#                         '--disable-dev-shm-usage',
#                         '--disable-blink-features=AutomationControlled'
#                     ]
#                 )
#                 
#                 # Create new page
#                 self.page = await self.browser.new_page()
#                 
#                 # Set headers
#                 await self.page.set_extra_http_headers({
#                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#                     'Accept': 'application/json, text/plain, */*',
#                     'Accept-Language': 'en-US,en;q=0.9',
#                     'Accept-Encoding': 'gzip, deflate, br',
#                     'Connection': 'keep-alive',
#                     'Referer': 'https://www.nseindia.com/'
#                 })
#                 
#                 # Add stealth script
#                 await self.page.add_init_script("""
#                     Object.defineProperty(navigator, 'webdriver', {
#                         get: () => undefined,
#                     });
#                 """)
#                 
#                 # Establish session by visiting homepage
#                 await self.page.goto("https://www.nseindia.com", wait_until='domcontentloaded')
#                 await asyncio.sleep(2)  # Wait for session to establish
#                 
#                 # Get cookies for aiohttp session
#                 cookies = await self.page.context.cookies()
#                 self.cookies = {cookie['name']: cookie['value'] for cookie in cookies}
#                 
#                 # Create aiohttp session with cookies
#                 self.session = aiohttp.ClientSession()
#                 
#                 self.is_initialized = True
#                 logger.info("✅ NSE session established with Playwright")
#                 return True
#                 
#             except Exception as e:
#                 logger.error(f"Failed to initialize NSE service: {e}")
#                 return False
#         
#         return True
#     
#     async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
#         """Get NSE quote using API calls with Playwright session"""
#         try:
#             if not await self._ensure_initialized():
#                 return None
#             
#             logger.info(f"📡 Calling NSE API for {symbol}...")
#             
#             # Call the quote API using aiohttp with cookies from Playwright
#             api_url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
#             
#             headers = {
#                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#                 "Accept": "application/json, text/plain, */*",
#                 "Accept-Language": "en-US,en;q=0.9",
#                 "Accept-Encoding": "gzip, deflate, br",
#                 "Connection": "keep-alive",
#                 "Referer": "https://www.nseindia.com/"
#             }
#             
#             async with self.session.get(api_url, headers=headers, cookies=self.cookies) as response:
#                 if response.status == 200:
#                     data = await response.json()
#                     
#                     # Extract price information
#                     price_info = data.get("priceInfo", {})
#                     if price_info:
#                         last_price = price_info.get("lastPrice", 0)
#                         change = price_info.get("change", 0)
#                         change_percent = price_info.get("pChange", 0)
#                         
#                         logger.info(f"✅ NSE API success for {symbol}: ₹{last_price}")
#                         
#                         return {
#                             "symbol": symbol,
#                             "last_price": last_price,
#                             "change": change,
#                             "change_percent": change_percent,
#                             "volume": price_info.get("totalTradedVolume", 0),
#                             "high": price_info.get("intraDayHighLow", {}).get("max", last_price),
#                             "low": price_info.get("intraDayHighLow", {}).get("min", last_price),
#                             "open": price_info.get("open", last_price),
#                             "previous_close": price_info.get("previousClose", last_price),
#                             "currency": "INR",
#                             "currency_symbol": "₹",
#                             "formatted_price": f"₹{last_price:,.2f}",
#                             "formatted_change": f"₹{change:,.2f}",
#                             "formatted_change_percent": f"{change_percent:.2f}%",
#                             "exchange": "NSE",
#                             "data_source": "NSE_WEB_SCRAPING",
#                             "timestamp": datetime.now().isoformat(),
#                             "reliability_level": "REAL_TIME"
#                         }
#                     else:
#                         logger.warning(f"No price info in API response for {symbol}")
#                         return None
#                 else:
#                     logger.error(f"NSE API failed for {symbol}: {response.status}")
#                     return None
#                     
#         except Exception as e:
#             logger.error(f"Error calling NSE API for {symbol}: {e}")
#             return None
#     
#     async def close(self):
#         """Close sessions and cleanup"""
#         try:
#             if self.session:
#                 await self.session.close()
#                 self.session = None
#             
#             if self.browser:
#                 await self.browser.close()
#                 self.browser = None
#             
#             if self.playwright:
#                 await self.playwright.stop()
#                 self.playwright = None
#             
#             self.is_initialized = False
#             logger.info("NSE API service closed")
#         except Exception as e:
#             logger.error(f"Error closing NSE service: {e}")

# Global instance - COMMENTED OUT
# nse_web_scraper = NSEWebScrapingService()

# Cleanup function - COMMENTED OUT
# async def cleanup_web_scraping():
#     """Cleanup web scraping resources"""
#     await nse_web_scraper.close()
