"""
Market Factors Service
Fetches and analyzes various market factors that affect stock prices:
- News (positive/negative with impact)
- Orderbook (buy/sell pressure)
- Block deals (bulk transactions)
- FII/DII flows (institutional investors)
- Insider trading
- Promoter holding changes
- Delivery percentage
- Open interest (for derivatives)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import os
import asyncio
from bs4 import BeautifulSoup
import re
from services.intelligent_stock_selector import IntelligentStockSelector
from services.sentiment_analysis import SentimentAnalysisService

logger = logging.getLogger(__name__)

class MarketFactorsService:
    """Service to fetch and analyze market factors affecting stocks"""
    
    def __init__(self):
        self.intelligent_selector = IntelligentStockSelector()
        self.sentiment_service = SentimentAnalysisService()
        self.nse_base_url = "https://www.nseindia.com"
        self.bse_base_url = "https://www.bseindia.com"
        # Cache for manual FII/DII data (key: date string, value: FII/DII data)
        self.manual_fii_dii_cache = {}
    
    async def get_market_factors(
        self,
        symbol: str,
        include_news: bool = True,
        include_orderbook: bool = True,
        include_block_deals: bool = True,
        include_fii_dii: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive market factors for a stock
        
        Returns:
            Dictionary with news, orderbook, block deals, FII/DII, and impact analysis
        """
        try:
            logger.info(f"📊 Fetching market factors for {symbol}...")
            
            factors = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "news": {},
                "orderbook": {},
                "block_deals": [],
                "fii_dii_flows": {},
                "insider_trading": [],
                "promoter_changes": {},
                "delivery_data": {},
                "impact_analysis": {}
            }
            
            # Fetch all factors in parallel
            tasks = []
            
            if include_news:
                tasks.append(self._fetch_stock_news(symbol))
            else:
                tasks.append(None)
            
            if include_orderbook:
                tasks.append(self._fetch_orderbook_data(symbol))
            else:
                tasks.append(None)
            
            if include_block_deals:
                tasks.append(self._fetch_block_deals(symbol))
            else:
                tasks.append(None)
            
            if include_fii_dii:
                tasks.append(self._fetch_fii_dii_flows(symbol))
            else:
                tasks.append(None)
            
            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            if results[0] and not isinstance(results[0], Exception):
                factors["news"] = results[0]
            
            if results[1] and not isinstance(results[1], Exception):
                factors["orderbook"] = results[1]
            
            if results[2] and not isinstance(results[2], Exception):
                factors["block_deals"] = results[2]
            
            if results[3] and not isinstance(results[3], Exception):
                factors["fii_dii_flows"] = results[3]
            
            # Fetch additional data
            factors["insider_trading"] = await self._fetch_insider_trading(symbol)
            factors["promoter_changes"] = await self._fetch_promoter_changes(symbol)
            factors["delivery_data"] = await self._fetch_delivery_data(symbol)
            
            # Analyze overall impact
            factors["impact_analysis"] = self._analyze_impact(factors)
            
            return factors
            
        except Exception as e:
            logger.error(f"Error fetching market factors for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _fetch_stock_news(self, symbol: str) -> Dict[str, Any]:
        """Fetch recent news for the stock"""
        try:
            # Use existing news fetching from intelligent selector
            news_items = await self.intelligent_selector._fetch_market_news()
            
            # Filter news relevant to this stock
            stock_news = []
            for news in news_items:
                title = news.get("title", "").lower()
                content = news.get("content", "").lower()
                symbol_lower = symbol.lower()
                
                # Check if news mentions the stock
                if symbol_lower in title or symbol_lower in content:
                    stock_news.append(news)
            
            # Analyze sentiment
            sentiment = self.sentiment_service.analyze_news_sentiment(stock_news)
            
            # Categorize news
            positive_news = [n for n in stock_news if n.get("sentiment") == "positive"]
            negative_news = [n for n in stock_news if n.get("sentiment") == "negative"]
            neutral_news = [n for n in stock_news if n.get("sentiment") == "neutral"]
            
            return {
                "total_news": len(stock_news),
                "positive_count": len(positive_news),
                "negative_count": len(negative_news),
                "neutral_count": len(neutral_news),
                "sentiment": sentiment.get("overall_sentiment", "neutral"),
                "sentiment_score": sentiment.get("score", 0),
                "recent_news": stock_news[:10],  # Last 10 news items
                "positive_news": positive_news[:5],
                "negative_news": negative_news[:5],
                "impact": self._calculate_news_impact(sentiment, len(stock_news))
            }
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return {"error": str(e)}
    
    async def _fetch_orderbook_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch orderbook data (buy/sell pressure)"""
        try:
            # Note: Real orderbook requires broker API or market data provider
            # For now, we'll use volume and price action as proxy
            
            from core.data_service import data_service
            quote = await data_service.get_quote(symbol, exchange="NSE")
            
            if not quote or "error" in quote:
                return {"error": "Unable to fetch quote data"}
            
            # Calculate buy/sell pressure indicators
            volume = float(quote.get("volume", 0))
            change = float(quote.get("change", 0))
            change_percent = float(quote.get("change_percent", 0))
            
            # Estimate orderbook pressure based on price action
            buy_pressure = "high" if change > 0 and change_percent > 1 else "medium" if change > 0 else "low"
            sell_pressure = "high" if change < 0 and abs(change_percent) > 1 else "medium" if change < 0 else "low"
            
            return {
                "volume": volume,
                "buy_pressure": buy_pressure,
                "sell_pressure": sell_pressure,
                "price_change": change,
                "price_change_percent": change_percent,
                "interpretation": self._interpret_orderbook_pressure(buy_pressure, sell_pressure, volume),
                "note": "Orderbook data estimated from price action. Real orderbook requires broker API."
            }
            
        except Exception as e:
            logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return {"error": str(e)}
    
    async def _fetch_block_deals(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch recent block deals - Try NSE first, then BSE"""
        try:
            block_deals = []
            
            # Priority 1: Scrape NSE
            try:
                nse_deals = await self._scrape_nse_block_deals(symbol)
                if nse_deals:
                    logger.info(f"✅ Found {len(nse_deals)} block deals from NSE for {symbol}")
                    return nse_deals
            except Exception as e:
                logger.warning(f"NSE block deals scraping failed for {symbol}: {e}")
            
            # Priority 2: Scrape BSE
            try:
                bse_deals = await self._scrape_bse_block_deals(symbol)
                if bse_deals:
                    logger.info(f"✅ Found {len(bse_deals)} block deals from BSE for {symbol}")
                    return bse_deals
            except Exception as e:
                logger.warning(f"BSE block deals scraping failed for {symbol}: {e}")
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching block deals for {symbol}: {e}")
            return []
    
    async def _scrape_nse_block_deals(self, symbol: str) -> List[Dict[str, Any]]:
        """Scrape block deals from NSE website"""
        try:
            # NSE Block Deals URL - requires proper session handling
            url = f"{self.nse_base_url}/market-data/block-deals"
            
            async with aiohttp.ClientSession() as session:
                # NSE requires proper headers and cookies
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                # First request to get cookies
                async with session.get(self.nse_base_url, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"NSE initial request failed: {response.status}")
                        return []
                
                # Now request block deals page
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find block deals table
                        # NSE structure may vary - adjust selectors as needed
                        deals = []
                        
                        # Look for table with block deals data
                        tables = soup.find_all('table')
                        for table in tables:
                            rows = table.find_all('tr')
                            if len(rows) > 1:  # Has header row
                                for row in rows[1:]:  # Skip header
                                    cells = row.find_all(['td', 'th'])
                                    if len(cells) >= 6:
                                        try:
                                            # Extract data from cells
                                            row_text = row.get_text()
                                            if symbol.upper() in row_text.upper():
                                                date_str = cells[0].get_text(strip=True)
                                                buyer = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                                                seller = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                                                quantity_str = cells[3].get_text(strip=True).replace(',', '').replace(' ', '')
                                                price_str = cells[4].get_text(strip=True).replace(',', '').replace('₹', '').replace(' ', '')
                                                value_str = cells[5].get_text(strip=True).replace(',', '').replace('₹', '').replace('Cr', '').replace(' ', '')
                                                
                                                # Parse numeric values
                                                quantity = int(float(quantity_str)) if quantity_str and quantity_str.replace('.', '').isdigit() else 0
                                                price = float(price_str) if price_str and price_str.replace('.', '').replace('-', '').isdigit() else 0
                                                value = float(value_str) if value_str and value_str.replace('.', '').replace('-', '').isdigit() else 0
                                                
                                                deals.append({
                                                    "date": date_str,
                                                    "buyer": buyer,
                                                    "seller": seller,
                                                    "quantity": quantity,
                                                    "price": price,
                                                    "value": value,
                                                    "type": "block",
                                                    "exchange": "NSE",
                                                    "symbol": symbol.upper()
                                                })
                                        except Exception as e:
                                            logger.debug(f"Error parsing block deal row: {e}")
                                            continue
                        
                        return deals[:20]  # Return last 20 deals
                    else:
                        logger.warning(f"NSE block deals request failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error scraping NSE block deals for {symbol}: {e}")
            return []
    
    async def _scrape_bse_block_deals(self, symbol: str) -> List[Dict[str, Any]]:
        """Scrape block deals from BSE website"""
        try:
            url = f"{self.bse_base_url}/markets/equity/EQReports/bulk_deals.aspx"
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                
                # BSE may require form submission with symbol
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        deals = []
                        
                        # Find bulk deals table
                        tables = soup.find_all('table', {'id': 'ctl00_ContentPlaceHolder1_gvbulk_deals'})
                        if not tables:
                            tables = soup.find_all('table')
                        
                        for table in tables:
                            rows = table.find_all('tr')
                            for row in rows[1:]:  # Skip header
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 6:
                                    try:
                                        row_text = row.get_text()
                                        if symbol.upper() in row_text.upper():
                                            date_str = cells[0].get_text(strip=True)
                                            buyer = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                                            seller = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                                            quantity_str = cells[3].get_text(strip=True).replace(',', '').replace(' ', '')
                                            price_str = cells[4].get_text(strip=True).replace(',', '').replace('₹', '').replace(' ', '')
                                            value_str = cells[5].get_text(strip=True).replace(',', '').replace('₹', '').replace('Cr', '').replace(' ', '')
                                            
                                            quantity = int(float(quantity_str)) if quantity_str and quantity_str.replace('.', '').isdigit() else 0
                                            price = float(price_str) if price_str and price_str.replace('.', '').replace('-', '').isdigit() else 0
                                            value = float(value_str) if value_str and value_str.replace('.', '').replace('-', '').isdigit() else 0
                                            
                                            deals.append({
                                                "date": date_str,
                                                "buyer": buyer,
                                                "seller": seller,
                                                "quantity": quantity,
                                                "price": price,
                                                "value": value,
                                                "type": "bulk",
                                                "exchange": "BSE",
                                                "symbol": symbol.upper()
                                            })
                                    except Exception as e:
                                        logger.debug(f"Error parsing BSE block deal row: {e}")
                                        continue
                        
                        return deals[:20]
                    else:
                        logger.warning(f"BSE block deals request failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error scraping BSE block deals for {symbol}: {e}")
            return []
    
    def set_manual_fii_dii_data(
        self,
        fii_net_investment: float,
        dii_net_investment: float,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set manual FII/DII data (for when automatic scraping fails)
        
        Args:
            fii_net_investment: FII net investment in Crores
            dii_net_investment: DII net investment in Crores
            date: Date string (YYYY-MM-DD). If None, uses today's date
            
        Returns:
            Dictionary with the stored data
        """
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            trend = self._determine_fii_dii_trend(fii_net_investment, dii_net_investment)
            
            data = {
                "fii_net_investment": float(fii_net_investment),
                "dii_net_investment": float(dii_net_investment),
                "fii_holding_percent": 0,
                "dii_holding_percent": 0,
                "trend": trend,
                "data_source": "MANUAL",
                "last_updated": datetime.now().isoformat(),
                "date": date
            }
            
            self.manual_fii_dii_cache[date] = data
            logger.info(f"✅ Manual FII/DII data set for {date}: FII={fii_net_investment} Cr, DII={dii_net_investment} Cr")
            
            return data
            
        except Exception as e:
            logger.error(f"Error setting manual FII/DII data: {e}")
            return {"error": str(e)}
    
    def get_manual_fii_dii_data(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get manual FII/DII data for a specific date
        
        Args:
            date: Date string (YYYY-MM-DD). If None, uses today's date
            
        Returns:
            FII/DII data if available, None otherwise
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        return self.manual_fii_dii_cache.get(date)
    
    async def _fetch_fii_dii_flows(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch FII/DII flows - Try manual data first, then multiple sources (NSE, NSDL, Moneycontrol)
        FII (Foreign Institutional Investors) and DII (Domestic Institutional Investors) 
        data indicates institutional money flow which significantly impacts stock prices.
        """
        try:
            # Check for manual data first
            today = datetime.now().strftime("%Y-%m-%d")
            manual_data = self.get_manual_fii_dii_data(today)
            if manual_data:
                logger.info(f"✅ Using manual FII/DII data for {today}")
                return manual_data
            
            # Try multiple sources in order of preference
            sources = [
                ("NSE", self._fetch_fii_dii_from_nse),
                ("NSDL", self._fetch_fii_dii_from_nsdl),
                ("Moneycontrol", self._fetch_fii_dii_from_moneycontrol)
            ]
            
            for source_name, fetch_func in sources:
                try:
                    result = await fetch_func()
                    if result and (result.get("fii_net_investment", 0) != 0 or result.get("dii_net_investment", 0) != 0):
                        logger.info(f"✅ Successfully fetched FII/DII data from {source_name}")
                        return result
                except Exception as e:
                    logger.debug(f"Failed to fetch from {source_name}: {e}")
                    continue
            
            # If all sources fail, return empty structure with helpful message
            logger.warning("⚠️ All FII/DII data sources failed. This may be due to:")
            logger.warning("   1. Website structure changes")
            logger.warning("   2. Anti-scraping measures")
            logger.warning("   3. Network/timeout issues")
            logger.warning("   4. Data not yet published for today")
            logger.warning("   Manual check: https://www.nseindia.com/market-data/fii-dii-data")
            return {
                "fii_net_investment": 0,
                "dii_net_investment": 0,
                "fii_holding_percent": 0,
                "dii_holding_percent": 0,
                "trend": "neutral",
                "data_source": "NONE",
                "last_updated": datetime.now().isoformat(),
                "note": "FII/DII data not available. This may be due to website changes, anti-scraping measures, or data not yet published. Check manually at: https://www.nseindia.com/market-data/fii-dii-data",
                "error": "All data sources failed. Web scraping may be blocked or website structure changed."
            }
                        
        except Exception as e:
            logger.error(f"Error fetching FII/DII flows for {symbol}: {e}")
            return {
                "fii_net_investment": 0,
                "dii_net_investment": 0,
                "trend": "neutral",
                "data_source": "ERROR",
                "error": str(e)
            }
    
    async def _fetch_fii_dii_from_nse(self) -> Dict[str, Any]:
        """Fetch FII/DII data from NSE website - Try multiple API endpoints, then web scraping"""
        try:
            # Method 1: Try NSE API endpoints (multiple variations)
            api_endpoints = [
                f"{self.nse_base_url}/api/fii-dii-data",
                f"{self.nse_base_url}/api/market-data/fii-dii-data",
                f"{self.nse_base_url}/api/reports/fii-dii",
                f"{self.nse_base_url}/api/reports/fii-dii-data",
                # Try NSE's actual data API endpoint
                f"{self.nse_base_url}/api/reports/fii-dii-data?date={datetime.now().strftime('%d-%m-%Y')}",
                f"{self.nse_base_url}/api/reports/fii-dii-data?date={datetime.now().strftime('%Y-%m-%d')}",
            ]
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': self.nse_base_url
                }
                
                # First, get session cookies by visiting NSE homepage
                try:
                    async with session.get(self.nse_base_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as cookie_response:
                        pass  # Just to get cookies
                except Exception:
                    pass
                
                # Try multiple API endpoints
                for api_url in api_endpoints:
                    try:
                        async with session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            if response.status == 200:
                                try:
                                    data = await response.json()
                                    # Parse API response (structure may vary)
                                    if isinstance(data, dict):
                                        fii_net = data.get("fii_net", data.get("fiiNetInvestment", 0))
                                        dii_net = data.get("dii_net", data.get("diiNetInvestment", 0))
                                        if fii_net != 0 or dii_net != 0:
                                            logger.info(f"✅ Successfully fetched FII/DII from NSE API")
                                            return {
                                                "fii_net_investment": float(fii_net),
                                                "dii_net_investment": float(dii_net),
                                                "fii_holding_percent": 0,
                                                "dii_holding_percent": 0,
                                                "trend": self._determine_fii_dii_trend(float(fii_net), float(dii_net)),
                                                "data_source": "NSE_API",
                                                "last_updated": datetime.now().isoformat()
                                            }
                                except Exception:
                                    pass  # API not available, try web scraping
                    except Exception:
                        pass  # API failed, try web scraping
                
                # Method 2: Web scraping fallback
                url = f"{self.nse_base_url}/market-data/fii-dii-data"
                
                # First request to get cookies
                async with session.get(self.nse_base_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logger.warning(f"NSE base URL returned status {response.status}")
                        return {}
                
                # Request FII/DII data page
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        fii_net = 0
                        dii_net = 0
                        
                        # Try to find FII/DII data in various formats
                        # Method 1: Look for tables
                        tables = soup.find_all('table')
                        for table in tables:
                            rows = table.find_all('tr')
                            if len(rows) > 1:
                                for row in rows[1:6]:  # Check first 5 data rows
                                    cells = row.find_all(['td', 'th'])
                                    if len(cells) >= 3:
                                        try:
                                            row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                                            # Look for FII and DII patterns
                                            fii_match = re.search(r'FII[:\s]*([-+]?\d+[.,]?\d*)', row_text, re.IGNORECASE)
                                            dii_match = re.search(r'DII[:\s]*([-+]?\d+[.,]?\d*)', row_text, re.IGNORECASE)
                                            
                                            if fii_match:
                                                fii_net = float(fii_match.group(1).replace(',', ''))
                                            if dii_match:
                                                dii_net = float(dii_match.group(1).replace(',', ''))
                                            
                                            if not fii_match and not dii_match:
                                                # Try parsing cells directly
                                                fii_str = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                                                dii_str = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                                                
                                                # Clean and parse
                                                fii_str = fii_str.replace(',', '').replace('₹', '').replace('Cr', '').replace(' ', '').replace('(', '-').replace(')', '')
                                                dii_str = dii_str.replace(',', '').replace('₹', '').replace('Cr', '').replace(' ', '').replace('(', '-').replace(')', '')
                                                
                                                try:
                                                    fii_val = float(fii_str) if fii_str and re.match(r'^-?\d+\.?\d*$', fii_str) else 0
                                                    dii_val = float(dii_str) if dii_str and re.match(r'^-?\d+\.?\d*$', dii_str) else 0
                                                    
                                                    if fii_val != 0:
                                                        fii_net = fii_val
                                                    if dii_val != 0:
                                                        dii_net = dii_val
                                                except ValueError:
                                                    continue
                                        except Exception as e:
                                            logger.debug(f"Error parsing row: {e}")
                                            continue
                        
                        # If we found data, return it
                        if fii_net != 0 or dii_net != 0:
                            logger.info(f"✅ Successfully scraped FII/DII from NSE: FII={fii_net}, DII={dii_net}")
                            trend = self._determine_fii_dii_trend(fii_net, dii_net)
                            return {
                                "fii_net_investment": fii_net,
                                "dii_net_investment": dii_net,
                                "fii_holding_percent": 0,
                                "dii_holding_percent": 0,
                                "trend": trend,
                                "data_source": "NSE",
                                "last_updated": datetime.now().isoformat()
                            }
                        else:
                            logger.warning("⚠️ NSE scraping succeeded but no FII/DII data found in HTML")
                            return {}
                    else:
                        logger.warning(f"⚠️ NSE FII/DII page returned status {response.status}")
                        return {}
                        
        except Exception as e:
            logger.warning(f"⚠️ Error fetching FII/DII from NSE: {str(e)}")
            return {}
    
    async def _fetch_fii_dii_from_nsdl(self) -> Dict[str, Any]:
        """Fetch FII/DII data from NSDL (National Securities Depository Limited)"""
        try:
            # NSDL FII data URL
            url = "https://www.nsdl.co.in/otc/fii-dii-data.php"
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        fii_net = 0
                        dii_net = 0
                        
                        # Parse NSDL data
                        tables = soup.find_all('table')
                        for table in tables:
                            rows = table.find_all('tr')
                            for row in rows[1:6]:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 3:
                                    try:
                                        fii_str = cells[1].get_text(strip=True).replace(',', '').replace('₹', '').replace('Cr', '')
                                        dii_str = cells[2].get_text(strip=True).replace(',', '').replace('₹', '').replace('Cr', '')
                                        
                                        fii_val = float(fii_str) if fii_str and re.match(r'^-?\d+\.?\d*$', fii_str.replace('-', '')) else 0
                                        dii_val = float(dii_str) if dii_str and re.match(r'^-?\d+\.?\d*$', dii_str.replace('-', '')) else 0
                                        
                                        if fii_val != 0:
                                            fii_net = fii_val
                                        if dii_val != 0:
                                            dii_net = dii_val
                                    except (ValueError, IndexError):
                                        continue
                        
                        trend = self._determine_fii_dii_trend(fii_net, dii_net)
                        
                        return {
                            "fii_net_investment": fii_net,
                            "dii_net_investment": dii_net,
                            "trend": trend,
                            "data_source": "NSDL",
                            "last_updated": datetime.now().isoformat()
                        }
                    else:
                        return {}
                        
        except Exception as e:
            logger.debug(f"Error fetching from NSDL: {e}")
            return {}
    
    async def _fetch_fii_dii_from_moneycontrol(self) -> Dict[str, Any]:
        """Fetch FII/DII data from Moneycontrol"""
        try:
            url = "https://www.moneycontrol.com/news/business/markets/fii-dii-data.html"
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        # Parse Moneycontrol format
                        # This is a fallback - Moneycontrol format may vary
                        fii_match = re.search(r'FII[:\s]*([-+]?\d+[.,]?\d*)\s*(?:crore|cr)', html, re.IGNORECASE)
                        dii_match = re.search(r'DII[:\s]*([-+]?\d+[.,]?\d*)\s*(?:crore|cr)', html, re.IGNORECASE)
                        
                        fii_net = float(fii_match.group(1).replace(',', '')) if fii_match else 0
                        dii_net = float(dii_match.group(1).replace(',', '')) if dii_match else 0
                        
                        trend = self._determine_fii_dii_trend(fii_net, dii_net)
                        
                        return {
                            "fii_net_investment": fii_net,
                            "dii_net_investment": dii_net,
                            "trend": trend,
                            "data_source": "Moneycontrol",
                            "last_updated": datetime.now().isoformat()
                        }
                    else:
                        return {}
                        
        except Exception as e:
            logger.debug(f"Error fetching from Moneycontrol: {e}")
            return {}
    
    def _determine_fii_dii_trend(self, fii_net: float, dii_net: float) -> str:
        """Determine trend based on FII and DII net investment"""
        if fii_net == 0 and dii_net == 0:
            return "neutral"
        elif fii_net > 0 and dii_net > 0:
            return "very_positive"
        elif fii_net < 0 and dii_net < 0:
            return "very_negative"
        elif fii_net > 0 or dii_net > 0:
            return "positive"
        elif fii_net < 0 or dii_net < 0:
            return "negative"
        else:
            return "neutral"
    
    async def _fetch_insider_trading(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch insider trading data"""
        try:
            # Insider trading data from SEBI disclosures
            return [
                {
                    "date": datetime.now().date().isoformat(),
                    "person": "Insider",
                    "transaction_type": "buy/sell",
                    "quantity": 0,
                    "price": 0,
                    "note": "Insider trading data requires SEBI disclosure scraping."
                }
            ]
            
        except Exception as e:
            logger.error(f"Error fetching insider trading for {symbol}: {e}")
            return []
    
    async def _fetch_promoter_changes(self, symbol: str) -> Dict[str, Any]:
        """Fetch promoter holding changes"""
        try:
            # Promoter holding data from shareholding patterns
            return {
                "current_holding": 0,
                "previous_holding": 0,
                "change": 0,
                "trend": "stable",
                "note": "Promoter holding data available from shareholding pattern analysis."
            }
            
        except Exception as e:
            logger.error(f"Error fetching promoter changes for {symbol}: {e}")
            return {}
    
    async def _fetch_delivery_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch delivery percentage data"""
        try:
            # Delivery data indicates quality of buying
            return {
                "delivery_percent": 0,
                "average_delivery": 0,
                "interpretation": "Delivery data indicates buying quality. High delivery = strong buying interest.",
                "note": "Delivery data requires NSE/BSE data scraping."
            }
            
        except Exception as e:
            logger.error(f"Error fetching delivery data for {symbol}: {e}")
            return {}
    
    def _calculate_news_impact(self, sentiment: Dict, news_count: int) -> str:
        """Calculate impact of news on stock price"""
        sentiment_score = sentiment.get("score", 0)
        overall_sentiment = sentiment.get("overall_sentiment", "neutral")
        
        if news_count == 0:
            return "No recent news"
        
        if overall_sentiment == "positive" and sentiment_score > 0.5:
            if news_count >= 5:
                return "Very High - Multiple positive news items"
            else:
                return "High - Positive news sentiment"
        elif overall_sentiment == "negative" and sentiment_score < -0.5:
            if news_count >= 5:
                return "Very High - Multiple negative news items"
            else:
                return "High - Negative news sentiment"
        else:
            return "Moderate - Mixed news sentiment"
    
    def _interpret_orderbook_pressure(self, buy_pressure: str, sell_pressure: str, volume: int) -> str:
        """Interpret orderbook buy/sell pressure"""
        if buy_pressure == "high" and sell_pressure == "low":
            return "Strong buying interest - Bullish signal"
        elif sell_pressure == "high" and buy_pressure == "low":
            return "Strong selling pressure - Bearish signal"
        elif buy_pressure == "high" and sell_pressure == "high":
            return "High volatility - Both sides active"
        else:
            return "Moderate activity - Neutral"
    
    def _analyze_impact(self, factors: Dict) -> Dict[str, Any]:
        """
        Analyze overall impact of all market factors on stock price.
        
        Impact Score Calculation:
        - News Sentiment: +2 (positive) / -2 (negative)
        - Orderbook Pressure: +1.5 (high buy) / -1.5 (high sell)
        - Block Deals: +1 (if any recent deals)
        - FII Net Investment: +2 (>100 Cr buy) / -2 (<-100 Cr sell)
        - DII Net Investment: +1.5 (>100 Cr buy) / -1.5 (<-100 Cr sell)
        
        Overall Impact Levels:
        - Very Positive: Score >= 3
        - Positive: Score >= 1
        - Neutral: Score between -1 and 1
        - Negative: Score <= -1
        - Very Negative: Score <= -3
        """
        impact_score = 0.0
        impact_factors = []
        detailed_breakdown = {}
        
        # 1. News Impact (Weight: 2.0)
        news = factors.get("news", {})
        news_sentiment = news.get("sentiment", "neutral")
        news_score = 0
        if news_sentiment == "positive":
            news_score = 2.0
            impact_score += news_score
            impact_factors.append(f"Positive news sentiment (Score: +{news_score})")
        elif news_sentiment == "negative":
            news_score = -2.0
            impact_score += news_score
            impact_factors.append(f"Negative news sentiment (Score: {news_score})")
        detailed_breakdown["news"] = {
            "sentiment": news_sentiment,
            "score": news_score,
            "weight": "High (2.0)"
        }
        
        # 2. Orderbook Impact (Weight: 1.5)
        orderbook = factors.get("orderbook", {})
        buy_pressure = orderbook.get("buy_pressure", "low")
        sell_pressure = orderbook.get("sell_pressure", "low")
        orderbook_score = 0
        if buy_pressure == "high":
            orderbook_score = 1.5
            impact_score += orderbook_score
            impact_factors.append(f"High buying pressure (Score: +{orderbook_score})")
        elif sell_pressure == "high":
            orderbook_score = -1.5
            impact_score += orderbook_score
            impact_factors.append(f"High selling pressure (Score: {orderbook_score})")
        detailed_breakdown["orderbook"] = {
            "buy_pressure": buy_pressure,
            "sell_pressure": sell_pressure,
            "score": orderbook_score,
            "weight": "Medium (1.5)"
        }
        
        # 3. Block Deals Impact (Weight: 1.0)
        block_deals = factors.get("block_deals", [])
        block_deals_score = 0
        if len(block_deals) > 0:
            block_deals_score = 1.0
            impact_score += block_deals_score
            impact_factors.append(f"{len(block_deals)} recent block deal(s) (Score: +{block_deals_score})")
        detailed_breakdown["block_deals"] = {
            "count": len(block_deals),
            "score": block_deals_score,
            "weight": "Medium (1.0)"
        }
        
        # 4. FII/DII Impact (Weight: FII=2.0, DII=1.5)
        fii_dii = factors.get("fii_dii_flows", {})
        fii_net = fii_dii.get("fii_net_investment", 0)
        dii_net = fii_dii.get("dii_net_investment", 0)
        
        fii_score = 0
        dii_score = 0
        
        # FII Impact (higher weight as FII flows are more significant)
        if fii_net > 100:  # More than 100 Cr buying
            fii_score = 2.0
            impact_score += fii_score
            impact_factors.append(f"Strong FII buying: ₹{fii_net:.2f} Cr (Score: +{fii_score})")
        elif fii_net < -100:  # More than 100 Cr selling
            fii_score = -2.0
            impact_score += fii_score
            impact_factors.append(f"Strong FII selling: ₹{abs(fii_net):.2f} Cr (Score: {fii_score})")
        elif fii_net > 0:
            fii_score = 0.5
            impact_score += fii_score
            impact_factors.append(f"Moderate FII buying: ₹{fii_net:.2f} Cr (Score: +{fii_score})")
        elif fii_net < 0:
            fii_score = -0.5
            impact_score += fii_score
            impact_factors.append(f"Moderate FII selling: ₹{abs(fii_net):.2f} Cr (Score: {fii_score})")
        
        # DII Impact
        if dii_net > 100:
            dii_score = 1.5
            impact_score += dii_score
            impact_factors.append(f"Strong DII buying: ₹{dii_net:.2f} Cr (Score: +{dii_score})")
        elif dii_net < -100:
            dii_score = -1.5
            impact_score += dii_score
            impact_factors.append(f"Strong DII selling: ₹{abs(dii_net):.2f} Cr (Score: {dii_score})")
        elif dii_net > 0:
            dii_score = 0.5
            impact_score += dii_score
            impact_factors.append(f"Moderate DII buying: ₹{dii_net:.2f} Cr (Score: +{dii_score})")
        elif dii_net < 0:
            dii_score = -0.5
            impact_score += dii_score
            impact_factors.append(f"Moderate DII selling: ₹{abs(dii_net):.2f} Cr (Score: {dii_score})")
        
        detailed_breakdown["fii_dii"] = {
            "fii_net_investment": fii_net,
            "dii_net_investment": dii_net,
            "fii_score": fii_score,
            "dii_score": dii_score,
            "fii_weight": "High (2.0)",
            "dii_weight": "Medium (1.5)",
            "explanation": "FII flows have higher weight as they represent foreign institutional money which significantly impacts market sentiment."
        }
        
        # Determine overall impact
        if impact_score >= 3:
            overall_impact = "Very Positive"
            impact_description = "Multiple strong positive factors indicate significant upward price pressure."
        elif impact_score >= 1:
            overall_impact = "Positive"
            impact_description = "Positive factors outweigh negative ones, suggesting upward price movement."
        elif impact_score <= -3:
            overall_impact = "Very Negative"
            impact_description = "Multiple strong negative factors indicate significant downward price pressure."
        elif impact_score <= -1:
            overall_impact = "Negative"
            impact_description = "Negative factors outweigh positive ones, suggesting downward price movement."
        else:
            overall_impact = "Neutral"
            impact_description = "Mixed signals with no clear directional bias. Price movement likely to be range-bound."
        
        return {
            "overall_impact": overall_impact,
            "impact_score": round(impact_score, 2),
            "impact_factors": impact_factors,
            "detailed_breakdown": detailed_breakdown,
            "summary": f"Market factors indicate {overall_impact.lower()} impact on stock price. {impact_description}",
            "calculation_explanation": {
                "method": "Weighted scoring system",
                "factors_considered": ["News Sentiment", "Orderbook Pressure", "Block Deals", "FII Flows", "DII Flows"],
                "score_range": "Very Negative (≤-3) to Very Positive (≥3)",
                "interpretation": f"Current score of {round(impact_score, 2)} indicates {overall_impact.lower()} impact."
            }
        }

# Create singleton instance
market_factors_service = MarketFactorsService()

