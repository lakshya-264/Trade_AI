"""
NSE & BSE Stock List Web Scraper
Fetches complete stock lists from NSE and BSE websites
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import re
import csv
from io import StringIO
import os

logger = logging.getLogger(__name__)

class NSEBSEStockScraper:
    def __init__(self):
        self.session = None
        self.is_initialized = False
        
        # Cache for stock lists
        self.stock_cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def _ensure_initialized(self):
        """Initialize aiohttp session if not already done"""
        if not self.is_initialized or self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
            self.is_initialized = True
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.is_initialized = False
    
    async def get_nse_stock_list(self) -> List[Dict[str, Any]]:
        """Fetch complete NSE stock list"""
        try:
            await self._ensure_initialized()
            
            # Check cache first
            cache_key = "nse_stocks"
            if cache_key in self.stock_cache:
                cached_data, timestamp = self.stock_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    logger.info("Using cached NSE stock list")
                    return cached_data
            
            logger.info("📈 Fetching NSE stock list from web scraper...")

            # Local file fallback (recommended when NSE blocks automated downloads)
            local_csv_path = os.getenv("NSE_EQUITY_CSV_PATH")
            if local_csv_path:
                try:
                    if os.path.exists(local_csv_path) and os.path.isfile(local_csv_path):
                        with open(local_csv_path, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read()
                        reader = csv.DictReader(StringIO(text))
                        local_stocks: List[Dict[str, Any]] = []
                        for row in reader:
                            # Normalize headers (NSE CSV sometimes has leading spaces in column names)
                            row_n = {str(k).strip(): v for k, v in (row or {}).items()}

                            symbol = (row_n.get("SYMBOL") or "").strip().upper()
                            name = (row_n.get("NAME OF COMPANY") or "").strip()
                            series = (row_n.get("SERIES") or "").strip().upper()

                            if not symbol or series not in {"EQ", "BE", "BZ", "SM", "ST"}:
                                continue

                            local_stocks.append({
                                "symbol": symbol,
                                "name": name or symbol,
                                "exchange": "NSE",
                                "sector": "",
                                "market_cap": 0,
                                "last_price": 0,
                                "change": 0,
                                "change_percent": 0,
                                "volume": 0,
                                "yahoo_symbol": f"{symbol}.NS",
                                "isin": (row_n.get("ISIN NUMBER") or "").strip(),
                                "series": series,
                                "listing_date": (row_n.get("DATE OF LISTING") or "").strip(),
                                "paid_up_value": (row_n.get("PAID UP VALUE") or "").strip(),
                                "market_lot": (row_n.get("MARKET LOT") or "").strip(),
                            })

                        if len(local_stocks) >= 1000:
                            logger.info(f"✅ Loaded {len(local_stocks)} NSE stocks from local EQUITY_L.csv: {local_csv_path}")
                            self.stock_cache[cache_key] = (local_stocks, datetime.now().timestamp())
                            return local_stocks
                        logger.warning(f"Local EQUITY_L.csv had only {len(local_stocks)} rows (expected ~2000+): {local_csv_path}")
                except Exception as e:
                    logger.warning(f"Failed to load local NSE EQUITY_L.csv from {local_csv_path}: {e}")

            # Primary source: NSE equity master list (all equity symbols)
            # This CSV typically contains ~2000+ listed equity symbols.
            # NSE uses Akamai and may block direct requests unless cookies are warmed up.
            csv_urls = [
                "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
                "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
                "https://www.nseindia.com/content/equities/EQUITY_L.csv",
            ]

            timeout = aiohttp.ClientTimeout(total=30)
            stocks: List[Dict[str, Any]] = []

            try:
                # Warm up cookies (helps bypass Akamai 503 blocks)
                try:
                    await self.session.get(
                        "https://www.nseindia.com",
                        timeout=aiohttp.ClientTimeout(total=10),
                        headers={"Referer": "https://www.nseindia.com/"},
                    )
                except Exception:
                    pass

                csv_headers = {
                    "Accept": "text/csv,application/csv,text/plain,*/*",
                    "Referer": "https://www.nseindia.com/",
                }

                for csv_url in csv_urls:
                    for attempt in range(2):
                        try:
                            async with self.session.get(csv_url, timeout=timeout, headers=csv_headers) as response:
                                if response.status != 200:
                                    logger.warning(f"EQUITY_L.csv fetch failed ({response.status}) from {csv_url}")
                                    continue

                                text = await response.text()
                                reader = csv.DictReader(StringIO(text))
                                tmp: List[Dict[str, Any]] = []
                                for row in reader:
                                    # Normalize headers (NSE CSV sometimes has leading spaces in column names)
                                    row_n = {str(k).strip(): v for k, v in (row or {}).items()}

                                    symbol = (row_n.get("SYMBOL") or "").strip().upper()
                                    name = (row_n.get("NAME OF COMPANY") or "").strip()
                                    series = (row_n.get("SERIES") or "").strip().upper()

                                    # Keep common equity series only
                                    if not symbol or series not in {"EQ", "BE", "BZ", "SM", "ST"}:
                                        continue

                                    tmp.append({
                                        "symbol": symbol,
                                        "name": name or symbol,
                                        "exchange": "NSE",
                                        "sector": "",
                                        "market_cap": 0,
                                        "last_price": 0,
                                        "change": 0,
                                        "change_percent": 0,
                                        "volume": 0,
                                        "yahoo_symbol": f"{symbol}.NS",
                                        "isin": (row_n.get("ISIN NUMBER") or "").strip(),
                                        "series": series,
                                        "listing_date": (row_n.get("DATE OF LISTING") or "").strip(),
                                        "paid_up_value": (row_n.get("PAID UP VALUE") or "").strip(),
                                        "market_lot": (row_n.get("MARKET LOT") or "").strip(),
                                    })

                                # Require a minimum size to consider it valid
                                if len(tmp) >= 1000:
                                    stocks = tmp
                                    logger.info(f"✅ Successfully fetched {len(stocks)} NSE stocks from EQUITY_L.csv ({csv_url})")
                                    break
                                else:
                                    logger.warning(f"EQUITY_L.csv parsed only {len(tmp)} rows from {csv_url} (attempt {attempt+1})")
                        except Exception as e:
                            logger.warning(f"Error fetching NSE EQUITY_L.csv from {csv_url} (attempt {attempt+1}): {e}")
                        await asyncio.sleep(0.5)

                    if stocks:
                        break
            except Exception as csv_err:
                logger.warning(f"Error fetching NSE EQUITY_L.csv: {csv_err}")

            # Fallback: NSE API endpoint for F&O list (limited universe)
            if not stocks:
                url = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"
                async with self.session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'data' in data:
                            for item in data['data']:
                                symbol = item.get('symbol', '')
                                stock_info = {
                                    'symbol': symbol,
                                    'name': item.get('companyName', '') or symbol,
                                    'exchange': 'NSE',
                                    'sector': item.get('industry', ''),
                                    'market_cap': item.get('marketCap', 0),
                                    'last_price': item.get('lastPrice', 0),
                                    'change': item.get('change', 0),
                                    'change_percent': item.get('pChange', 0),
                                    'volume': item.get('totalTradedVolume', 0),
                                    'yahoo_symbol': f"{symbol}.NS"
                                }
                                stocks.append(stock_info)
                        logger.info(f"✅ Successfully fetched {len(stocks)} NSE stocks from F&O list (fallback)")
                    else:
                        logger.error(f"NSE API returned status {response.status}")
                        return []

            # Cache the result
            self.stock_cache[cache_key] = (stocks, datetime.now().timestamp())
            return stocks
                    
        except Exception as e:
            logger.error(f"Error fetching NSE stock list: {e}")
            return []
    
    async def get_bse_stock_list(self) -> List[Dict[str, Any]]:
        """Fetch complete BSE stock list using multiple approaches"""
        try:
            await self._ensure_initialized()
            
            # Check cache first
            cache_key = "bse_stocks"
            if cache_key in self.stock_cache:
                cached_data, timestamp = self.stock_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    logger.info("Using cached BSE stock list")
                    return cached_data
            
            logger.info("📈 Fetching BSE stock list from web scraper...")
            
            # Try multiple BSE API endpoints
            bse_urls = [
                "https://api.bseindia.com/BseIndiaAPI/api/StockReachGraph/w?scripcode=&flag=0&fromdate=&todate=&seriesid=",
                "https://www.bseindia.com/api/StockReachGraph/w?scripcode=&flag=0&fromdate=&todate=&seriesid=",
                "https://api.bseindia.com/BseIndiaAPI/api/StockReachGraph/w",
                "https://www.bseindia.com/stock-share-price/SiteCache/StockReachGraph.aspx"
            ]
            
            stocks = []
            timeout = aiohttp.ClientTimeout(total=30)
            
            for url in bse_urls:
                try:
                    logger.info(f"Trying BSE URL: {url}")
                    async with self.session.get(url, timeout=timeout) as response:
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if response.status == 200:
                            if 'application/json' in content_type:
                                # Try to parse as JSON
                                try:
                                    data = await response.json()
                                    stocks = self._parse_bse_json_data(data)
                                    if stocks:
                                        logger.info(f"✅ Successfully fetched {len(stocks)} BSE stocks from JSON API")
                                        break
                                except Exception as json_error:
                                    logger.warning(f"JSON parsing failed: {json_error}")
                            
                            elif 'text/html' in content_type:
                                # Try to parse HTML for stock data
                                try:
                                    html_content = await response.text()
                                    stocks = self._parse_bse_html_data(html_content)
                                    if stocks:
                                        logger.info(f"✅ Successfully fetched {len(stocks)} BSE stocks from HTML")
                                        break
                                except Exception as html_error:
                                    logger.warning(f"HTML parsing failed: {html_error}")
                            
                            else:
                                logger.warning(f"Unexpected content type: {content_type}")
                        else:
                            logger.warning(f"BSE API returned status {response.status} for {url}")
                            
                except Exception as url_error:
                    logger.warning(f"Error with URL {url}: {url_error}")
                    continue
            
            # If no stocks found from APIs, use a fallback list of major BSE stocks
            if not stocks:
                logger.info("Using fallback BSE stock list")
                stocks = self._get_fallback_bse_stocks()
            
            # Cache the result
            self.stock_cache[cache_key] = (stocks, datetime.now().timestamp())
            
            logger.info(f"✅ Total BSE stocks fetched: {len(stocks)}")
            return stocks
                    
        except Exception as e:
            logger.error(f"Error fetching BSE stock list: {e}")
            # Return fallback stocks on error
            return self._get_fallback_bse_stocks()
    
    def _parse_bse_json_data(self, data) -> List[Dict[str, Any]]:
        """Parse BSE JSON response"""
        stocks = []
        try:
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        stock_info = {
                            'symbol': str(item.get('scrip_cd', '')),
                            'name': str(item.get('scrip_name', '')),
                            'exchange': 'BSE',
                            'sector': str(item.get('industry', '')),
                            'market_cap': float(item.get('market_cap', 0)),
                            'last_price': str(item.get('last_price', '0')),
                            'change': float(item.get('change', 0)),
                            'change_percent': float(item.get('change_percent', 0)),
                            'volume': int(item.get('volume', 0)),
                            'yahoo_symbol': f"{item.get('scrip_cd', '')}.BO"
                        }
                        if stock_info['symbol']:  # Only add if symbol exists
                            stocks.append(stock_info)
        except Exception as e:
            logger.error(f"Error parsing BSE JSON data: {e}")
        
        return stocks
    
    def _parse_bse_html_data(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse BSE HTML response for stock data"""
        stocks = []
        try:
            # Look for JSON data embedded in HTML
            import re
            import json
            
            # Try to find JSON data in script tags or data attributes
            json_patterns = [
                r'var\s+stockData\s*=\s*(\[.*?\]);',
                r'window\.stockData\s*=\s*(\[.*?\]);',
                r'data-stocks\s*=\s*"([^"]*)"',
                r'<script[^>]*>.*?(\[.*?\])',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        # Clean up the match
                        clean_match = match.replace('\\"', '"').replace("\\'", "'")
                        data = json.loads(clean_match)
                        stocks = self._parse_bse_json_data(data)
                        if stocks:
                            break
                    except:
                        continue
                        
        except Exception as e:
            logger.error(f"Error parsing BSE HTML data: {e}")
        
        return stocks
    
    def _get_fallback_bse_stocks(self) -> List[Dict[str, Any]]:
        """Get fallback list of major BSE stocks when API fails"""
        return [
            {
                'symbol': 'RELIANCE',
                'name': 'Reliance Industries Ltd',
                'exchange': 'BSE',
                'sector': 'Energy',
                'market_cap': 0,
                'last_price': '0',
                'change': 0,
                'change_percent': 0,
                'volume': 0,
                'yahoo_symbol': 'RELIANCE.BO'
            },
            {
                'symbol': 'TCS',
                'name': 'Tata Consultancy Services Ltd',
                'exchange': 'BSE',
                'sector': 'Technology',
                'market_cap': 0,
                'last_price': '0',
                'change': 0,
                'change_percent': 0,
                'volume': 0,
                'yahoo_symbol': 'TCS.BO'
            },
            {
                'symbol': 'HDFCBANK',
                'name': 'HDFC Bank Ltd',
                'exchange': 'BSE',
                'sector': 'Banking',
                'market_cap': 0,
                'last_price': '0',
                'change': 0,
                'change_percent': 0,
                'volume': 0,
                'yahoo_symbol': 'HDFCBANK.BO'
            },
            {
                'symbol': 'INFY',
                'name': 'Infosys Ltd',
                'exchange': 'BSE',
                'sector': 'Technology',
                'market_cap': 0,
                'last_price': '0',
                'change': 0,
                'change_percent': 0,
                'volume': 0,
                'yahoo_symbol': 'INFY.BO'
            },
            {
                'symbol': 'ITC',
                'name': 'ITC Ltd',
                'exchange': 'BSE',
                'sector': 'FMCG',
                'market_cap': 0,
                'last_price': '0',
                'change': 0,
                'change_percent': 0,
                'volume': 0,
                'yahoo_symbol': 'ITC.BO'
            }
        ]
    
    async def get_all_stocks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch all NSE and BSE stocks"""
        try:
            logger.info("🚀 Fetching complete NSE & BSE stock lists...")
            
            # Fetch both lists in parallel
            nse_task = asyncio.create_task(self.get_nse_stock_list())
            bse_task = asyncio.create_task(self.get_bse_stock_list())
            
            nse_stocks, bse_stocks = await asyncio.gather(nse_task, bse_task)
            
            result = {
                'nse': nse_stocks,
                'bse': bse_stocks,
                'total_nse': len(nse_stocks),
                'total_bse': len(bse_stocks),
                'total_stocks': len(nse_stocks) + len(bse_stocks),
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Total stocks fetched: {result['total_stocks']} (NSE: {result['total_nse']}, BSE: {result['total_bse']})")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching all stocks: {e}")
            return {'nse': [], 'bse': [], 'total_nse': 0, 'total_bse': 0, 'total_stocks': 0, 'error': str(e)}
    
    async def search_stocks(self, query: str, exchange: str = 'ALL') -> List[Dict[str, Any]]:
        """Search stocks by symbol or name"""
        try:
            all_stocks = await self.get_all_stocks()
            
            query = query.upper().strip()
            results = []
            
            # Search in NSE stocks
            if exchange in ['ALL', 'NSE']:
                for stock in all_stocks['nse']:
                    if (query in stock['symbol'].upper() or 
                        query in stock['name'].upper()):
                        results.append(stock)
            
            # Search in BSE stocks
            if exchange in ['ALL', 'BSE']:
                for stock in all_stocks['bse']:
                    if (query in stock['symbol'].upper() or 
                        query in stock['name'].upper()):
                        results.append(stock)
            
            # Remove duplicates (same symbol in both exchanges)
            seen_symbols = set()
            unique_results = []
            for stock in results:
                if stock['symbol'] not in seen_symbols:
                    unique_results.append(stock)
                    seen_symbols.add(stock['symbol'])
            
            logger.info(f"🔍 Found {len(unique_results)} stocks matching '{query}'")
            return unique_results
            
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []
    
    async def get_stock_by_symbol(self, symbol: str, exchange: str = 'NSE') -> Optional[Dict[str, Any]]:
        """Get specific stock details by symbol"""
        try:
            all_stocks = await self.get_all_stocks()
            
            symbol = symbol.upper().strip()
            
            # Search in NSE stocks
            if exchange in ['ALL', 'NSE']:
                for stock in all_stocks['nse']:
                    if stock['symbol'] == symbol:
                        return stock
            
            # Search in BSE stocks
            if exchange in ['ALL', 'BSE']:
                for stock in all_stocks['bse']:
                    if stock['symbol'] == symbol:
                        return stock
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting stock by symbol: {e}")
            return None

# Global instance
nse_bse_scraper = NSEBSEStockScraper()

async def cleanup_nse_bse_scraper():
    """Cleanup function"""
    await nse_bse_scraper.close()
