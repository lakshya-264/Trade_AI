"""
Screener.in Web Scraper Service
Fetches comprehensive company data from screener.in
100% Legal - Public data from screener.in website
Reference: https://www.screener.in/company/RELIANCE/consolidated/
"""

import logging
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)

class ScreenerScraper:
    """Scrape company data from screener.in"""
    
    # Symbol mapping: NSE symbol -> Screener.in symbol
    # Some stocks have different symbols on Screener.in
    SCREENER_SYMBOL_MAP = {
        "NMDC": "NMDC",
        "INFIBEAM": "INFIBEAM",  # May need to check actual symbol
        "INDIANREN": "IREDA",  # Indian Renewable Energy Development Agency
        "BSE": "BSE",
        "TANLA": "TANLA",
        "BIRLASOFT": "BIRLASOFT",
        "COALINDIA": "COALINDIA",
        "SUZLON": "SUZLON",
        "SAKSOFT": "SAKSOFT",
        "GAIL": "GAIL",
        "ADANIGREEN": "ADANIGREEN",
        "NHPC": "NHPC",
        "COCHINSHIP": "COCHINSHIP",
        "IRFC": "IRFC",
        "IRB": "IRB",
        "BAJAJHLDNG": "BAJAJHLDNG",  # May need to check
        "HGIEL": "HGIEL",  # May need to check
        # Common variations
        "BAJAJ-AUTO": "BAJAJAUTO",
        "M&M": "M&M",
        "L&T": "L&T",
    }
    
    def __init__(self):
        self.session = None
        self.base_url = "https://www.screener.in"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.screener.in/"
        }
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
    
    def _normalize_symbol_for_screener(self, symbol: str) -> str:
        """
        Normalize symbol for Screener.in URL
        Some stocks have different symbols on Screener.in vs NSE
        """
        if not symbol:
            return symbol
        
        symbol_upper = symbol.upper().strip()
        
        # Check mapping first
        if symbol_upper in self.SCREENER_SYMBOL_MAP:
            return self.SCREENER_SYMBOL_MAP[symbol_upper]
        
        # Default: use symbol as-is (Screener.in usually uses uppercase)
        return symbol_upper
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _parse_number(self, text: str) -> Optional[float]:
        """Parse number from text, handling Indian number format"""
        if not text or text == 'N/A' or text == '-':
            return None
        
        # Remove currency symbols and commas
        text = text.replace('₹', '').replace(',', '').replace(' ', '')
        
        # Handle percentage
        if '%' in text:
            text = text.replace('%', '')
            try:
                return float(text)
            except:
                return None
        
        # Handle Cr (Crores)
        if 'Cr' in text or 'Cr.' in text:
            text = text.replace('Cr', '').replace('Cr.', '').strip()
            try:
                return float(text) * 10000  # Convert to lakhs for consistency
            except:
                return None
        
        # Handle regular numbers
        try:
            return float(text)
        except:
            return None
    
    def _extract_key_metrics(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract key financial metrics from the page"""
        metrics = {}
        
        try:
            # Find the key metrics section
            # Screener.in displays metrics in a specific format
            metric_sections = soup.find_all(['div', 'span'], class_=re.compile(r'company|metric|ratio', re.I))
            
            # Look for specific metric patterns
            # Market Cap, Current Price, PE Ratio, etc.
            text_content = soup.get_text()
            
            # Extract Market Cap
            market_cap_match = re.search(r'Market Cap\s*₹?\s*([\d,]+\.?\d*)\s*Cr', text_content, re.I)
            if market_cap_match:
                metrics['market_cap'] = self._parse_number(market_cap_match.group(1))
            
            # Extract Current Price
            price_match = re.search(r'Current Price\s*₹?\s*([\d,]+\.?\d*)', text_content, re.I)
            if price_match:
                metrics['current_price'] = self._parse_number(price_match.group(1))
            
            # Extract PE Ratio
            pe_match = re.search(r'Stock P/E|P/E Ratio|PE\s*([\d,]+\.?\d*)', text_content, re.I)
            if pe_match:
                metrics['pe_ratio'] = self._parse_number(pe_match.group(1))
            
            # Extract Book Value
            bv_match = re.search(r'Book Value\s*₹?\s*([\d,]+\.?\d*)', text_content, re.I)
            if bv_match:
                metrics['book_value'] = self._parse_number(bv_match.group(1))
            
            # Extract Dividend Yield
            div_match = re.search(r'Dividend Yield\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if div_match:
                metrics['dividend_yield'] = self._parse_number(div_match.group(1))
            
            # Extract ROCE
            roce_match = re.search(r'ROCE\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if roce_match:
                metrics['roce'] = self._parse_number(roce_match.group(1))
            
            # Extract ROE
            roe_match = re.search(r'ROE\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if roe_match:
                metrics['roe'] = self._parse_number(roe_match.group(1))
            
            # Extract 52 Week High/Low
            high_low_match = re.search(r'High\s*/\s*Low\s*₹\s*([\d,]+\.?\d*)\s*/\s*([\d,]+\.?\d*)', text_content, re.I)
            if high_low_match:
                metrics['52_week_high'] = self._parse_number(high_low_match.group(1))
                metrics['52_week_low'] = self._parse_number(high_low_match.group(2))
            
        except Exception as e:
            logger.error(f"Error extracting key metrics: {e}")
        
        return metrics
    
    def _extract_quarterly_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract quarterly results table with comprehensive field mapping"""
        quarters = []
        
        try:
            # Find quarterly results section - Screener.in uses specific IDs/classes
            # Look for section with "Quarterly" or "Quarters" in heading
            quarterly_section = None
            for heading in soup.find_all(['h2', 'h3', 'h4', 'div'], class_=lambda x: x and ('quarter' in x.lower() or 'results' in x.lower())):
                parent = heading.find_parent()
                if parent:
                    quarterly_section = parent
                    break
            
            # If no specific section found, search all tables
            search_area = quarterly_section if quarterly_section else soup
            tables = search_area.find_all('table')
            
            for table in tables:
                headers = table.find_all('th')
                if not headers:
                    continue
                
                # Get header text to identify quarterly P&L table
                header_texts = [h.get_text().strip().lower() for h in headers]
                header_text = ' '.join(header_texts)
                
                # Check if this is quarterly results table
                is_quarterly_table = any(keyword in header_text for keyword in [
                    'sales', 'revenue', 'quarter', 'period', 'profit', 'expenses'
                ])
                
                if not is_quarterly_table:
                    continue
                
                # Map column indices to field names
                column_map = {}
                for idx, header in enumerate(headers):
                    header_lower = header.get_text().strip().lower()
                    if any(x in header_lower for x in ['period', 'quarter', 'date']):
                        column_map['period'] = idx
                    elif any(x in header_lower for x in ['sales', 'revenue', 'income']):
                        column_map['revenue'] = idx
                    elif any(x in header_lower for x in ['expenses', 'cost']):
                        column_map['expenses'] = idx
                    elif any(x in header_lower for x in ['operating profit', 'ebit', 'pbit']):
                        column_map['ebit'] = idx
                    elif any(x in header_lower for x in ['net profit', 'profit after tax', 'pat']):
                        column_map['net_profit'] = idx
                    elif any(x in header_lower for x in ['eps', 'earnings per share']):
                        column_map['eps'] = idx
                    elif any(x in header_lower for x in ['net worth', 'equity', 'shareholders']):
                        column_map['net_worth'] = idx
                
                if 'period' not in column_map:
                    continue  # Skip if we can't identify period column
                
                # Extract data rows
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) <= column_map.get('period', 0):
                        continue
                    
                    quarter_data = {}
                    try:
                        # Extract period (required)
                        period_idx = column_map.get('period', 0)
                        period = cells[period_idx].get_text().strip()
                        if not period or period.lower() in ['total', 'average', '']:
                            continue
                        quarter_data['period'] = period
                        
                        # Extract revenue/sales
                        if 'revenue' in column_map:
                            revenue_text = cells[column_map['revenue']].get_text().strip()
                            quarter_data['revenue'] = self._parse_number(revenue_text)
                            quarter_data['sales'] = quarter_data['revenue']  # Alias
                        
                        # Extract expenses
                        if 'expenses' in column_map:
                            expenses_text = cells[column_map['expenses']].get_text().strip()
                            quarter_data['expenses'] = self._parse_number(expenses_text)
                        
                        # Extract operating profit (EBIT)
                        if 'ebit' in column_map:
                            ebit_text = cells[column_map['ebit']].get_text().strip()
                            quarter_data['ebit'] = self._parse_number(ebit_text)
                            quarter_data['operating_profit'] = quarter_data['ebit']  # Alias
                        
                        # Extract net profit
                        if 'net_profit' in column_map:
                            profit_text = cells[column_map['net_profit']].get_text().strip()
                            quarter_data['net_profit'] = self._parse_number(profit_text)
                            quarter_data['profit'] = quarter_data['net_profit']  # Alias
                        
                        # Extract EPS
                        if 'eps' in column_map:
                            eps_text = cells[column_map['eps']].get_text().strip()
                            quarter_data['eps'] = self._parse_number(eps_text)
                            quarter_data['earnings_per_share'] = quarter_data['eps']  # Alias
                        
                        # Extract net worth
                        if 'net_worth' in column_map:
                            net_worth_text = cells[column_map['net_worth']].get_text().strip()
                            quarter_data['net_worth'] = self._parse_number(net_worth_text)
                        
                        # Only add if we have at least period and one financial metric
                        if quarter_data.get('period') and (
                            quarter_data.get('revenue') or 
                            quarter_data.get('net_profit') or 
                            quarter_data.get('ebit')
                        ):
                            quarters.append(quarter_data)
                    except Exception as e:
                        logger.debug(f"Error parsing quarter row: {e}")
                        continue
                
                # If we found quarters, stop searching
                if quarters:
                    break
        
        except Exception as e:
            logger.error(f"Error extracting quarterly results: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        logger.info(f"Extracted {len(quarters)} quarterly records")
        return quarters
    
    def _extract_shareholding(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract shareholding pattern"""
        shareholding = {}
        
        try:
            # Find shareholding table
            text_content = soup.get_text()
            
            # Extract Promoters holding
            promoters_match = re.search(r'Promoters\s*\+?\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if promoters_match:
                shareholding['promoters'] = self._parse_number(promoters_match.group(1))
            
            # Extract FIIs holding
            fii_match = re.search(r'FIIs\s*\+?\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if fii_match:
                shareholding['fiis'] = self._parse_number(fii_match.group(1))
            
            # Extract DIIs holding
            dii_match = re.search(r'DIIs\s*\+?\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if dii_match:
                shareholding['diis'] = self._parse_number(dii_match.group(1))
            
            # Extract Public holding
            public_match = re.search(r'Public\s*\+?\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if public_match:
                shareholding['public'] = self._parse_number(public_match.group(1))
        
        except Exception as e:
            logger.error(f"Error extracting shareholding: {e}")
        
        return shareholding
    
    def _extract_company_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract company overview and key information"""
        info = {}
        
        try:
            # Extract company name
            title = soup.find('title')
            if title:
                info['company_name'] = title.get_text().strip()
            
            # Extract about section
            about_section = soup.find('div', class_=re.compile(r'about|company-info', re.I))
            if about_section:
                info['about'] = about_section.get_text().strip()
            
            # Extract key points
            key_points = []
            key_points_section = soup.find('div', class_=re.compile(r'key-points|highlights', re.I))
            if key_points_section:
                points = key_points_section.find_all(['li', 'p'])
                for point in points:
                    text = point.get_text().strip()
                    if text:
                        key_points.append(text)
            
            if key_points:
                info['key_points'] = key_points
        
        except Exception as e:
            logger.error(f"Error extracting company info: {e}")
        
        return info
    
    def _extract_growth_metrics(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract growth metrics (Compounded Sales Growth, Profit Growth, Stock Price CAGR, ROE)"""
        growth_metrics = {}
        text_content = soup.get_text()
        
        try:
            # Compounded Sales Growth
            sales_10y = re.search(r'10 Years:\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if sales_10y:
                growth_metrics['sales_growth_10y'] = self._parse_number(sales_10y.group(1))
            
            sales_5y = re.search(r'5 Years:\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if sales_5y:
                growth_metrics['sales_growth_5y'] = self._parse_number(sales_5y.group(1))
            
            sales_3y = re.search(r'3 Years:\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if sales_3y:
                growth_metrics['sales_growth_3y'] = self._parse_number(sales_3y.group(1))
            
            sales_ttm = re.search(r'TTM:\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if sales_ttm:
                growth_metrics['sales_growth_ttm'] = self._parse_number(sales_ttm.group(1))
            
            # Compounded Profit Growth
            profit_10y = re.search(r'10 Years:\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if profit_10y:
                growth_metrics['profit_growth_10y'] = self._parse_number(profit_10y.group(1))
            
            # Stock Price CAGR
            price_10y = re.search(r'10 Years:\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if price_10y:
                growth_metrics['price_cagr_10y'] = self._parse_number(price_10y.group(1))
            
            # Return on Equity
            roe_10y = re.search(r'10 Years:\s*([\d,]+\.?\d*)\s*%', text_content, re.I)
            if roe_10y:
                growth_metrics['roe_10y'] = self._parse_number(roe_10y.group(1))
        
        except Exception as e:
            logger.error(f"Error extracting growth metrics: {e}")
        
        return growth_metrics
    
    def _extract_balance_sheet(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract balance sheet data (Equity Capital, Reserves, Borrowings)"""
        balance_sheet_data = []
        
        try:
            # Find balance sheet table
            tables = soup.find_all('table')
            
            for table in tables:
                headers = table.find_all('th')
                if not headers:
                    continue
                
                # Check if this is balance sheet table
                header_text = ' '.join([h.get_text() for h in headers])
                if 'Equity Capital' in header_text or 'Reserves' in header_text:
                    rows = table.find_all('tr')[1:]  # Skip header row
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 2:
                            continue
                        
                        try:
                            period = cells[0].get_text().strip()
                            equity_capital = self._parse_number(cells[1].get_text().strip()) if len(cells) > 1 else None
                            reserves = self._parse_number(cells[2].get_text().strip()) if len(cells) > 2 else None
                            borrowings = self._parse_number(cells[3].get_text().strip()) if len(cells) > 3 else None
                            
                            if period and (equity_capital or reserves or borrowings):
                                balance_sheet_data.append({
                                    'period': period,
                                    'equity_capital': equity_capital,
                                    'reserves': reserves,
                                    'borrowings': borrowings
                                })
                        except Exception as e:
                            logger.debug(f"Error parsing balance sheet row: {e}")
                            continue
                    
                    break  # Found balance sheet table
        
        except Exception as e:
            logger.error(f"Error extracting balance sheet: {e}")
        
        return balance_sheet_data
    
    def _extract_cash_flows(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract cash flow data"""
        cash_flow_data = []
        
        try:
            # Find cash flow table
            tables = soup.find_all('table')
            
            for table in tables:
                headers = table.find_all('th')
                if not headers:
                    continue
                
                # Check if this is cash flow table
                header_text = ' '.join([h.get_text() for h in headers])
                if 'Operating' in header_text and 'Cash' in header_text:
                    rows = table.find_all('tr')[1:]
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 2:
                            continue
                        
                        try:
                            period = cells[0].get_text().strip()
                            operating_cf = self._parse_number(cells[1].get_text().strip()) if len(cells) > 1 else None
                            investing_cf = self._parse_number(cells[2].get_text().strip()) if len(cells) > 2 else None
                            financing_cf = self._parse_number(cells[3].get_text().strip()) if len(cells) > 3 else None
                            
                            if period:
                                cash_flow_data.append({
                                    'period': period,
                                    'operating_cash_flow': operating_cf,
                                    'investing_cash_flow': investing_cf,
                                    'financing_cash_flow': financing_cf
                                })
                        except Exception as e:
                            logger.debug(f"Error parsing cash flow row: {e}")
                            continue
                    
                    break
        
        except Exception as e:
            logger.error(f"Error extracting cash flows: {e}")
        
        return cash_flow_data
    
    def _extract_detailed_shareholding(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract detailed shareholding pattern over time"""
        shareholding_data = []
        
        try:
            # Find shareholding table
            tables = soup.find_all('table')
            
            for table in tables:
                headers = table.find_all('th')
                if not headers:
                    continue
                
                # Check if this is shareholding table
                header_text = ' '.join([h.get_text() for h in headers])
                if 'Promoters' in header_text or 'FIIs' in header_text:
                    rows = table.find_all('tr')[1:]
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 2:
                            continue
                        
                        try:
                            period = cells[0].get_text().strip()
                            promoters = self._parse_number(cells[1].get_text().strip()) if len(cells) > 1 else None
                            fiis = self._parse_number(cells[2].get_text().strip()) if len(cells) > 2 else None
                            diis = self._parse_number(cells[3].get_text().strip()) if len(cells) > 3 else None
                            government = self._parse_number(cells[4].get_text().strip()) if len(cells) > 4 else None
                            public = self._parse_number(cells[5].get_text().strip()) if len(cells) > 5 else None
                            shareholders = None
                            if len(cells) > 6:
                                shareholders_text = cells[6].get_text().strip().replace(',', '')
                                try:
                                    shareholders = int(float(shareholders_text))
                                except:
                                    pass
                            
                            if period:
                                shareholding_data.append({
                                    'period': period,
                                    'promoters': promoters,
                                    'fiis': fiis,
                                    'diis': diis,
                                    'government': government,
                                    'public': public,
                                    'no_of_shareholders': shareholders
                                })
                        except Exception as e:
                            logger.debug(f"Error parsing shareholding row: {e}")
                            continue
                    
                    break
        
        except Exception as e:
            logger.error(f"Error extracting detailed shareholding: {e}")
        
        return shareholding_data
    
    async def get_company_data(self, symbol: str, consolidated: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive company data from screener.in
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            consolidated: Whether to fetch consolidated data (default: True)
        
        Returns:
            Dictionary with company data
        """
        original_symbol = symbol.upper().strip()
        
        # Normalize symbol for Screener.in
        screener_symbol = self._normalize_symbol_for_screener(original_symbol)
        
        try:
            # Check cache
            cache_key = f"{screener_symbol}_{'consolidated' if consolidated else 'standalone'}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if (datetime.now() - cached_time).seconds < self.cache_ttl:
                    logger.info(f"Returning cached data for {original_symbol} (Screener: {screener_symbol})")
                    # Update symbol in cached data to original
                    cached_data["symbol"] = original_symbol
                    return cached_data
            
            session = await self._get_session()
            
            # Construct URL with normalized symbol
            url_type = "consolidated" if consolidated else "standalone"
            url = f"{self.base_url}/company/{screener_symbol}/{url_type}/"
            
            logger.info(f"Fetching data from screener.in for {original_symbol} -> {screener_symbol} ({url_type})")
            
            # Try multiple variations if first attempt fails
            symbols_to_try = [screener_symbol]
            
            # Add lowercase variation
            if screener_symbol != screener_symbol.lower():
                symbols_to_try.append(screener_symbol.lower())
            
            # Add variations with common suffixes removed
            if screener_symbol.endswith("LTD") or screener_symbol.endswith("LIMITED"):
                base_symbol = screener_symbol.replace("LTD", "").replace("LIMITED", "").strip()
                symbols_to_try.append(base_symbol)
            
            last_error = None
            for try_symbol in symbols_to_try:
                try_url = f"{self.base_url}/company/{try_symbol}/{url_type}/"
                
                try:
                    async with session.get(try_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, "lxml")
                            # Check if page actually has data (not a 404 or error page)
                            page_text = soup.get_text().lower()
                            if "page not found" in page_text or "company not found" in page_text:
                                logger.warning(f"Page found but no data for {try_symbol}")
                                continue
                            # Extract all data
                            company_data = {
                                "symbol": original_symbol,  # Keep original symbol
                                "screener_symbol": try_symbol,  # Store actual Screener symbol used
                                "source": "screener.in",
                                "url": try_url,
                                "fetched_at": datetime.utcnow().isoformat(),
                                "consolidated": consolidated,
                                "key_metrics": self._extract_key_metrics(soup),
                                "company_info": self._extract_company_info(soup),
                                "quarterly_results": self._extract_quarterly_results(soup),
                                "shareholding": self._extract_shareholding(soup),
                                "growth_metrics": self._extract_growth_metrics(soup),
                                "balance_sheet": self._extract_balance_sheet(soup),
                                "cash_flows": self._extract_cash_flows(soup),
                                "detailed_shareholding": self._extract_detailed_shareholding(soup)
                            }
                            
                            # Cache the data
                            self.cache[cache_key] = (company_data, datetime.now())
                            
                            logger.info(f"Successfully fetched data for {original_symbol} using Screener symbol: {try_symbol}")
                            return company_data
                        else:
                            last_error = f"HTTP {response.status}"
                            logger.debug(f"Failed for {try_symbol}: {last_error}, trying next variation...")
                            continue
                except Exception as e:
                    last_error = str(e)
                    logger.debug(f"Error trying {try_symbol}: {last_error}, trying next variation...")
                    continue
            
            logger.warning(f"Failed to fetch data for {original_symbol} (tried: {', '.join(symbols_to_try)}): {last_error}")
            return {
                "symbol": original_symbol,
                "error": f"Not found on Screener.in (tried: {', '.join(symbols_to_try)})",
                "fetched_at": datetime.utcnow().isoformat()
                    }
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching data for {original_symbol}")
            return {
                "symbol": original_symbol,
                "error": "Request timeout",
                "fetched_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching data for {original_symbol}: {e}")
            return {
                "symbol": original_symbol,
                "error": str(e),
                "fetched_at": datetime.utcnow().isoformat()
            }
    
    async def get_financial_ratios(self, symbol: str) -> Dict[str, Any]:
        """
        Get financial ratios from screener.in
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Dictionary with financial ratios
        """
        company_data = await self.get_company_data(symbol)
        return company_data.get("key_metrics", {})
    
    async def get_quarterly_results(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get quarterly results from screener.in
        
        Args:
            symbol: Stock symbol
        
        Returns:
            List of quarterly results
        """
        company_data = await self.get_company_data(symbol)
        return company_data.get("quarterly_results", [])

# Create singleton instance
screener_scraper = ScreenerScraper()

