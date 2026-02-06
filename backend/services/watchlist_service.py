"""
Watchlist Service
Comprehensive watchlist management and symbol search for TradingView-style charting
Supports multiple watchlists, symbol search, popular symbols, and real-time updates
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
import json
import uuid
import asyncio
from enum import Enum
import re

logger = logging.getLogger(__name__)

class ExchangeType(Enum):
    NSE = "NSE"
    BSE = "BSE"
    MCX = "MCX"
    NCDEX = "NCDEX"
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"

class SymbolCategory(Enum):
    EQUITY = "equity"
    INDEX = "index"
    FUTURES = "futures"
    OPTIONS = "options"
    CURRENCY = "currency"
    COMMODITY = "commodity"
    CRYPTO = "crypto"

class WatchlistService:
    def __init__(self):
        # Watchlist storage (in production, this would be database)
        self.watchlists_storage = {}
        self.user_watchlists_index = {}
        
        # Symbol data (mock data for now)
        self.symbols_data = self._initialize_symbols_data()
        
        # Popular symbols cache
        self.popular_symbols_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Search index for fast symbol lookup
        self.search_index = self._build_search_index()
        
        # Real-time price updates
        self.price_updates = {}
        self.update_subscribers = {}
    
    def _initialize_symbols_data(self) -> Dict[str, Any]:
        """Initialize comprehensive symbol database"""
        return {
            # NSE Equity Stocks
            "RELIANCE": {
                "symbol": "RELIANCE",
                "name": "Reliance Industries Ltd",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.EQUITY.value,
                "sector": "Oil & Gas",
                "market_cap": "Large Cap",
                "isin": "INE002A01018",
                "description": "Integrated energy and petrochemicals company",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "TCS": {
                "symbol": "TCS",
                "name": "Tata Consultancy Services Ltd",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.EQUITY.value,
                "sector": "Information Technology",
                "market_cap": "Large Cap",
                "isin": "INE467B01029",
                "description": "Leading IT services and consulting company",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "HDFCBANK": {
                "symbol": "HDFCBANK",
                "name": "HDFC Bank Ltd",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.EQUITY.value,
                "sector": "Banking",
                "market_cap": "Large Cap",
                "isin": "INE040A01034",
                "description": "Leading private sector bank",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "INFY": {
                "symbol": "INFY",
                "name": "Infosys Ltd",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.EQUITY.value,
                "sector": "Information Technology",
                "market_cap": "Large Cap",
                "isin": "INE009A01021",
                "description": "Global technology services company",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "HINDUNILVR": {
                "symbol": "HINDUNILVR",
                "name": "Hindustan Unilever Ltd",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.EQUITY.value,
                "sector": "FMCG",
                "market_cap": "Large Cap",
                "isin": "INE030A01027",
                "description": "Leading FMCG company",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "ICICIBANK": {
                "symbol": "ICICIBANK",
                "name": "ICICI Bank Ltd",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.EQUITY.value,
                "sector": "Banking",
                "market_cap": "Large Cap",
                "isin": "INE090A01021",
                "description": "Leading private sector bank",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "KOTAKBANK": {
                "symbol": "KOTAKBANK",
                "name": "Kotak Mahindra Bank Ltd",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.EQUITY.value,
                "sector": "Banking",
                "market_cap": "Large Cap",
                "isin": "INE237A01028",
                "description": "Leading private sector bank",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "BHARTIARTL": {
                "symbol": "BHARTIARTL",
                "name": "Bharti Airtel Ltd",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.EQUITY.value,
                "sector": "Telecommunications",
                "market_cap": "Large Cap",
                "isin": "INE397D01024",
                "description": "Leading telecommunications company",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "ITC": {
                "symbol": "ITC",
                "name": "ITC Ltd",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.EQUITY.value,
                "sector": "FMCG",
                "market_cap": "Large Cap",
                "isin": "INE154A01025",
                "description": "Diversified conglomerate",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "SBIN": {
                "symbol": "SBIN",
                "name": "State Bank of India",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.EQUITY.value,
                "sector": "Banking",
                "market_cap": "Large Cap",
                "isin": "INE062A01020",
                "description": "Largest public sector bank",
                "is_active": True,
                "last_updated": datetime.now()
            },
            
            # NSE Indices
            "NIFTY_50": {
                "symbol": "NIFTY_50",
                "name": "Nifty 50",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.INDEX.value,
                "sector": "Index",
                "market_cap": "Index",
                "isin": "NIFTY50",
                "description": "NSE's benchmark index",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "NIFTY_BANK": {
                "symbol": "NIFTY_BANK",
                "name": "Nifty Bank",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.INDEX.value,
                "sector": "Banking",
                "market_cap": "Index",
                "isin": "NIFTYBANK",
                "description": "Banking sector index",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "NIFTY_IT": {
                "symbol": "NIFTY_IT",
                "name": "Nifty IT",
                "exchange": ExchangeType.NSE.value,
                "category": SymbolCategory.INDEX.value,
                "sector": "Information Technology",
                "market_cap": "Index",
                "isin": "NIFTYIT",
                "description": "IT sector index",
                "is_active": True,
                "last_updated": datetime.now()
            },
            
            # BSE Stocks
            "RELIANCE_BSE": {
                "symbol": "RELIANCE_BSE",
                "name": "Reliance Industries Ltd",
                "exchange": ExchangeType.BSE.value,
                "category": SymbolCategory.EQUITY.value,
                "sector": "Oil & Gas",
                "market_cap": "Large Cap",
                "isin": "INE002A01018",
                "description": "Integrated energy and petrochemicals company",
                "is_active": True,
                "last_updated": datetime.now()
            },
            
            # Forex Pairs
            "USDINR": {
                "symbol": "USDINR",
                "name": "USD/INR",
                "exchange": ExchangeType.FOREX.value,
                "category": SymbolCategory.CURRENCY.value,
                "sector": "Currency",
                "market_cap": "Forex",
                "isin": "USDINR",
                "description": "US Dollar vs Indian Rupee",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "EURINR": {
                "symbol": "EURINR",
                "name": "EUR/INR",
                "exchange": ExchangeType.FOREX.value,
                "category": SymbolCategory.CURRENCY.value,
                "sector": "Currency",
                "market_cap": "Forex",
                "isin": "EURINR",
                "description": "Euro vs Indian Rupee",
                "is_active": True,
                "last_updated": datetime.now()
            },
            
            # Crypto
            "BTCINR": {
                "symbol": "BTCINR",
                "name": "Bitcoin/INR",
                "exchange": ExchangeType.CRYPTO.value,
                "category": SymbolCategory.CRYPTO.value,
                "sector": "Cryptocurrency",
                "market_cap": "Crypto",
                "isin": "BTCINR",
                "description": "Bitcoin vs Indian Rupee",
                "is_active": True,
                "last_updated": datetime.now()
            },
            "ETHINR": {
                "symbol": "ETHINR",
                "name": "Ethereum/INR",
                "exchange": ExchangeType.CRYPTO.value,
                "category": SymbolCategory.CRYPTO.value,
                "sector": "Cryptocurrency",
                "market_cap": "Crypto",
                "isin": "ETHINR",
                "description": "Ethereum vs Indian Rupee",
                "is_active": True,
                "last_updated": datetime.now()
            }
        }
    
    def _build_search_index(self) -> Dict[str, List[str]]:
        """Build search index for fast symbol lookup"""
        search_index = {}
        
        for symbol, data in self.symbols_data.items():
            # Index by symbol
            search_index[symbol.lower()] = [symbol]
            
            # Index by name words
            name_words = data["name"].lower().split()
            for word in name_words:
                if word not in search_index:
                    search_index[word] = []
                search_index[word].append(symbol)
            
            # Index by sector
            sector = data["sector"].lower()
            if sector not in search_index:
                search_index[sector] = []
            search_index[sector].append(symbol)
            
            # Index by category
            category = data["category"].lower()
            if category not in search_index:
                search_index[category] = []
            search_index[category].append(symbol)
        
        return search_index
    
    async def create_watchlist(
        self,
        user_id: int,
        name: str,
        symbols: List[str] = None,
        is_default: bool = False
    ) -> str:
        """Create new watchlist"""
        try:
            # Validate symbols
            if symbols is None:
                symbols = []
            
            validated_symbols = []
            for symbol in symbols:
                if symbol in self.symbols_data:
                    validated_symbols.append(symbol)
                else:
                    logger.warning(f"Invalid symbol {symbol} skipped")
            
            # Generate unique watchlist ID
            watchlist_id = f"watchlist_{user_id}_{uuid.uuid4().hex[:8]}"
            
            # Create watchlist data
            watchlist_data = {
                "id": watchlist_id,
                "user_id": user_id,
                "name": name,
                "symbols": validated_symbols,
                "is_default": is_default,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "metadata": {
                    "version": "1.0",
                    "created_by": "charting_system"
                }
            }
            
            # Store watchlist
            self.watchlists_storage[watchlist_id] = watchlist_data
            
            # Add to user's watchlists index
            user_key = f"user_{user_id}"
            if user_key not in self.user_watchlists_index:
                self.user_watchlists_index[user_key] = []
            
            self.user_watchlists_index[user_key].append(watchlist_id)
            
            # If this is set as default, unset other defaults
            if is_default:
                await self._unset_other_defaults(user_id, watchlist_id)
            
            logger.info(f"Watchlist {watchlist_id} created for user {user_id}")
            return watchlist_id
            
        except Exception as e:
            logger.error(f"Error creating watchlist: {e}")
            raise
    
    async def get_user_watchlists(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's watchlists"""
        try:
            user_key = f"user_{user_id}"
            user_watchlist_ids = self.user_watchlists_index.get(user_key, [])
            
            watchlists = []
            for watchlist_id in user_watchlist_ids:
                if watchlist_id in self.watchlists_storage:
                    watchlist = self.watchlists_storage[watchlist_id]
                    # Add symbol details
                    watchlist["symbol_details"] = await self._get_symbol_details(watchlist["symbols"])
                    watchlists.append(watchlist)
            
            # Sort by creation time (newest first)
            watchlists.sort(key=lambda x: x["created_at"], reverse=True)
            
            logger.info(f"Retrieved {len(watchlists)} watchlists for user {user_id}")
            return watchlists
            
        except Exception as e:
            logger.error(f"Error getting user watchlists: {e}")
            return []
    
    async def get_watchlist(self, watchlist_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get specific watchlist by ID"""
        try:
            if watchlist_id not in self.watchlists_storage:
                return None
            
            watchlist = self.watchlists_storage[watchlist_id]
            if watchlist["user_id"] != user_id:
                return None
            
            # Add symbol details
            watchlist["symbol_details"] = await self._get_symbol_details(watchlist["symbols"])
            
            return watchlist
            
        except Exception as e:
            logger.error(f"Error getting watchlist {watchlist_id}: {e}")
            return None
    
    async def add_symbol(
        self,
        watchlist_id: str,
        symbol: str,
        user_id: int
    ) -> bool:
        """Add symbol to watchlist"""
        try:
            if watchlist_id not in self.watchlists_storage:
                return False
            
            watchlist = self.watchlists_storage[watchlist_id]
            if watchlist["user_id"] != user_id:
                return False
            
            # Validate symbol
            if symbol not in self.symbols_data:
                logger.warning(f"Invalid symbol {symbol}")
                return False
            
            # Check if symbol already exists
            if symbol in watchlist["symbols"]:
                logger.info(f"Symbol {symbol} already exists in watchlist")
                return True
            
            # Add symbol
            watchlist["symbols"].append(symbol)
            watchlist["updated_at"] = datetime.now()
            
            logger.info(f"Symbol {symbol} added to watchlist {watchlist_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding symbol to watchlist: {e}")
            return False
    
    async def remove_symbol(
        self,
        watchlist_id: str,
        symbol: str,
        user_id: int
    ) -> bool:
        """Remove symbol from watchlist"""
        try:
            if watchlist_id not in self.watchlists_storage:
                return False
            
            watchlist = self.watchlists_storage[watchlist_id]
            if watchlist["user_id"] != user_id:
                return False
            
            # Remove symbol
            if symbol in watchlist["symbols"]:
                watchlist["symbols"].remove(symbol)
                watchlist["updated_at"] = datetime.now()
                logger.info(f"Symbol {symbol} removed from watchlist {watchlist_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing symbol from watchlist: {e}")
            return False
    
    async def update_watchlist(
        self,
        watchlist_id: str,
        user_id: int,
        updates: Dict[str, Any]
    ) -> bool:
        """Update watchlist"""
        try:
            if watchlist_id not in self.watchlists_storage:
                return False
            
            watchlist = self.watchlists_storage[watchlist_id]
            if watchlist["user_id"] != user_id:
                return False
            
            # Update allowed fields
            allowed_fields = ["name", "symbols", "is_default"]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == "symbols":
                        # Validate symbols
                        validated_symbols = []
                        for symbol in value:
                            if symbol in self.symbols_data:
                                validated_symbols.append(symbol)
                        watchlist[field] = validated_symbols
                    else:
                        watchlist[field] = value
            
            watchlist["updated_at"] = datetime.now()
            
            # If this is set as default, unset other defaults
            if updates.get("is_default", False):
                await self._unset_other_defaults(user_id, watchlist_id)
            
            logger.info(f"Watchlist {watchlist_id} updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating watchlist: {e}")
            return False
    
    async def delete_watchlist(self, watchlist_id: str, user_id: int) -> bool:
        """Delete watchlist"""
        try:
            if watchlist_id not in self.watchlists_storage:
                return False
            
            watchlist = self.watchlists_storage[watchlist_id]
            if watchlist["user_id"] != user_id:
                return False
            
            # Remove from storage
            del self.watchlists_storage[watchlist_id]
            
            # Remove from user index
            user_key = f"user_{user_id}"
            if user_key in self.user_watchlists_index:
                user_watchlists = self.user_watchlists_index[user_key]
                if watchlist_id in user_watchlists:
                    user_watchlists.remove(watchlist_id)
            
            logger.info(f"Watchlist {watchlist_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting watchlist: {e}")
            return False
    
    async def search_symbols(
        self,
        query: str,
        exchange: str = ExchangeType.NSE.value,
        limit: int = 20,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for symbols"""
        try:
            query_lower = query.lower().strip()
            if not query_lower:
                return []
            
            results = []
            seen_symbols = set()
            
            # Search in index
            for search_term, symbols in self.search_index.items():
                if query_lower in search_term:
                    for symbol in symbols:
                        if symbol not in seen_symbols:
                            symbol_data = self.symbols_data[symbol]
                            
                            # Filter by exchange
                            if exchange and symbol_data["exchange"] != exchange:
                                continue
                            
                            # Filter by category
                            if category and symbol_data["category"] != category:
                                continue
                            
                            # Calculate relevance score
                            score = self._calculate_relevance_score(query_lower, symbol_data)
                            
                            results.append({
                                **symbol_data,
                                "relevance_score": score
                            })
                            seen_symbols.add(symbol)
            
            # Sort by relevance score and limit results
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            results = results[:limit]
            
            logger.info(f"Found {len(results)} symbols matching '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching symbols: {e}")
            return []
    
    async def get_popular_symbols(
        self,
        exchange: str = ExchangeType.NSE.value,
        limit: int = 20,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get popular/most traded symbols"""
        try:
            cache_key = f"popular_{exchange}_{category or 'all'}_{limit}"
            
            # Check cache
            if cache_key in self.popular_symbols_cache:
                cached_data, timestamp = self.popular_symbols_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self.cache_ttl:
                    return cached_data
            
            # Get popular symbols (mock implementation)
            popular_symbols = [
                "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
                "ICICIBANK", "KOTAKBANK", "BHARTIARTL", "ITC", "SBIN",
                "NIFTY_50", "NIFTY_BANK", "NIFTY_IT"
            ]
            
            results = []
            for symbol in popular_symbols[:limit]:
                if symbol in self.symbols_data:
                    symbol_data = self.symbols_data[symbol]
                    
                    # Filter by exchange
                    if exchange and symbol_data["exchange"] != exchange:
                        continue
                    
                    # Filter by category
                    if category and symbol_data["category"] != category:
                        continue
                    
                    results.append(symbol_data)
            
            # Cache the results
            self.popular_symbols_cache[cache_key] = (results, datetime.now().timestamp())
            
            logger.info(f"Retrieved {len(results)} popular symbols")
            return results
            
        except Exception as e:
            logger.error(f"Error getting popular symbols: {e}")
            return []
    
    async def get_symbol_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a symbol"""
        try:
            if symbol not in self.symbols_data:
                return None
            
            symbol_data = self.symbols_data[symbol].copy()
            
            # Add real-time price data (mock)
            symbol_data["current_price"] = await self._get_current_price(symbol)
            symbol_data["price_change"] = await self._get_price_change(symbol)
            symbol_data["price_change_percent"] = await self._get_price_change_percent(symbol)
            symbol_data["volume"] = await self._get_volume(symbol)
            symbol_data["last_updated"] = datetime.now()
            
            return symbol_data
            
        except Exception as e:
            logger.error(f"Error getting symbol details for {symbol}: {e}")
            return None
    
    async def get_symbols_by_sector(self, sector: str, exchange: str = ExchangeType.NSE.value) -> List[Dict[str, Any]]:
        """Get symbols by sector"""
        try:
            results = []
            
            for symbol, data in self.symbols_data.items():
                if (data["sector"].lower() == sector.lower() and 
                    data["exchange"] == exchange and 
                    data["is_active"]):
                    results.append(data)
            
            logger.info(f"Found {len(results)} symbols in sector {sector}")
            return results
            
        except Exception as e:
            logger.error(f"Error getting symbols by sector: {e}")
            return []
    
    async def get_symbols_by_category(self, category: str, exchange: str = ExchangeType.NSE.value) -> List[Dict[str, Any]]:
        """Get symbols by category"""
        try:
            results = []
            
            for symbol, data in self.symbols_data.items():
                if (data["category"].lower() == category.lower() and 
                    data["exchange"] == exchange and 
                    data["is_active"]):
                    results.append(data)
            
            logger.info(f"Found {len(results)} symbols in category {category}")
            return results
            
        except Exception as e:
            logger.error(f"Error getting symbols by category: {e}")
            return []
    
    async def subscribe_to_price_updates(self, user_id: int, symbols: List[str]):
        """Subscribe to real-time price updates"""
        try:
            user_key = f"user_{user_id}"
            if user_key not in self.update_subscribers:
                self.update_subscribers[user_key] = set()
            
            for symbol in symbols:
                self.update_subscribers[user_key].add(symbol)
            
            logger.info(f"User {user_id} subscribed to price updates for {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error subscribing to price updates: {e}")
    
    async def unsubscribe_from_price_updates(self, user_id: int, symbols: List[str]):
        """Unsubscribe from real-time price updates"""
        try:
            user_key = f"user_{user_id}"
            if user_key in self.update_subscribers:
                for symbol in symbols:
                    self.update_subscribers[user_key].discard(symbol)
            
            logger.info(f"User {user_id} unsubscribed from price updates for {len(symbols)} symbols")
            
        except Exception as e:
            logger.error(f"Error unsubscribing from price updates: {e}")
    
    def _calculate_relevance_score(self, query: str, symbol_data: Dict[str, Any]) -> float:
        """Calculate relevance score for search results"""
        try:
            score = 0.0
            
            # Exact symbol match
            if query == symbol_data["symbol"].lower():
                score += 100.0
            
            # Symbol starts with query
            elif symbol_data["symbol"].lower().startswith(query):
                score += 50.0
            
            # Symbol contains query
            elif query in symbol_data["symbol"].lower():
                score += 25.0
            
            # Name exact match
            if query == symbol_data["name"].lower():
                score += 80.0
            
            # Name starts with query
            elif symbol_data["name"].lower().startswith(query):
                score += 40.0
            
            # Name contains query
            elif query in symbol_data["name"].lower():
                score += 20.0
            
            # Sector match
            if query in symbol_data["sector"].lower():
                score += 10.0
            
            # Category match
            if query in symbol_data["category"].lower():
                score += 5.0
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.0
    
    async def _get_symbol_details(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get details for multiple symbols"""
        try:
            details = []
            for symbol in symbols:
                symbol_detail = await self.get_symbol_details(symbol)
                if symbol_detail:
                    details.append(symbol_detail)
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting symbol details: {e}")
            return []
    
    async def _unset_other_defaults(self, user_id: int, current_watchlist_id: str):
        """Unset other default watchlists for user"""
        try:
            user_key = f"user_{user_id}"
            user_watchlist_ids = self.user_watchlists_index.get(user_key, [])
            
            for watchlist_id in user_watchlist_ids:
                if (watchlist_id != current_watchlist_id and 
                    watchlist_id in self.watchlists_storage):
                    watchlist = self.watchlists_storage[watchlist_id]
                    if watchlist["is_default"]:
                        watchlist["is_default"] = False
                        watchlist["updated_at"] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error unsetting other defaults: {e}")
    
    async def _get_current_price(self, symbol: str) -> float:
        """Get current price for symbol (mock implementation)"""
        try:
            # Mock price data
            base_prices = {
                "RELIANCE": 2450.50,
                "TCS": 3850.75,
                "HDFCBANK": 1650.20,
                "INFY": 1850.30,
                "HINDUNILVR": 2650.80,
                "ICICIBANK": 950.45,
                "KOTAKBANK": 1850.60,
                "BHARTIARTL": 850.25,
                "ITC": 450.80,
                "SBIN": 650.40,
                "NIFTY_50": 19500.50,
                "NIFTY_BANK": 45000.75,
                "NIFTY_IT": 35000.25,
                "USDINR": 83.25,
                "EURINR": 90.50,
                "BTCINR": 3500000.00,
                "ETHINR": 250000.00
            }
            
            base_price = base_prices.get(symbol, 100.0)
            
            # Add some random variation
            import random
            variation = random.uniform(-0.02, 0.02)  # ±2% variation
            current_price = base_price * (1 + variation)
            
            return round(current_price, 2)
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0
    
    async def _get_price_change(self, symbol: str) -> float:
        """Get price change for symbol (mock implementation)"""
        try:
            # Mock price change
            import random
            change = random.uniform(-50, 50)
            return round(change, 2)
            
        except Exception as e:
            logger.error(f"Error getting price change for {symbol}: {e}")
            return 0.0
    
    async def _get_price_change_percent(self, symbol: str) -> float:
        """Get price change percentage for symbol (mock implementation)"""
        try:
            # Mock price change percentage
            import random
            change_percent = random.uniform(-5, 5)
            return round(change_percent, 2)
            
        except Exception as e:
            logger.error(f"Error getting price change percent for {symbol}: {e}")
            return 0.0
    
    async def _get_volume(self, symbol: str) -> int:
        """Get volume for symbol (mock implementation)"""
        try:
            # Mock volume data
            import random
            volume = random.randint(100000, 10000000)
            return volume
            
        except Exception as e:
            logger.error(f"Error getting volume for {symbol}: {e}")
            return 0
    
    def get_exchanges(self) -> List[Dict[str, str]]:
        """Get list of available exchanges"""
        return [
            {"value": exchange.value, "name": exchange.value, "description": f"{exchange.value} Exchange"}
            for exchange in ExchangeType
        ]
    
    def get_categories(self) -> List[Dict[str, str]]:
        """Get list of available categories"""
        return [
            {"value": category.value, "name": category.value.title(), "description": f"{category.value.title()} instruments"}
            for category in SymbolCategory
        ]
    
    def get_sectors(self) -> List[str]:
        """Get list of available sectors"""
        sectors = set()
        for symbol_data in self.symbols_data.values():
            sectors.add(symbol_data["sector"])
        return sorted(list(sectors))
    
    def is_available(self) -> bool:
        """Check if service is available"""
        try:
            # Test basic functionality
            test_symbol = "RELIANCE"
            return test_symbol in self.symbols_data
        except Exception:
            return False
    
    def clear_storage(self):
        """Clear all watchlists storage (for testing)"""
        self.watchlists_storage.clear()
        self.user_watchlists_index.clear()
        self.popular_symbols_cache.clear()
        self.price_updates.clear()
        self.update_subscribers.clear()
        logger.info("Watchlist storage cleared")
