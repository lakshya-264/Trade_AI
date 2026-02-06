"""
On-Chain Metrics Data Ingestion Service
Handles blockchain/crypto data for alternative market analysis
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import aiohttp
import json

logger = logging.getLogger(__name__)

class OnChainMetricsIngestion:
    def __init__(self):
        self.metrics_data = {}
        self.crypto_symbols = ["BTC", "ETH", "BNB", "ADA", "SOL", "DOT", "MATIC", "AVAX"]
        
        # On-chain metrics to track
        self.metrics = {
            "network_activity": ["active_addresses", "transaction_count", "network_hash_rate"],
            "market_metrics": ["market_cap", "trading_volume", "price_volatility"],
            "sentiment_indicators": ["fear_greed_index", "social_volume", "whale_activity"],
            "technical_indicators": ["mvrv_ratio", "nvt_ratio", "realized_cap", "supply_in_profit"]
        }
        
        # Data storage
        self.data_buffer_size = 1000
        self.update_interval = 300  # 5 minutes
        
    async def start_onchain_monitoring(self):
        """Start monitoring on-chain metrics"""
        try:
            while True:
                await self._collect_all_metrics()
                await asyncio.sleep(self.update_interval)
                
        except Exception as e:
            logger.error(f"Error in on-chain monitoring: {e}")
    
    async def _collect_all_metrics(self):
        """Collect all on-chain metrics"""
        try:
            tasks = []
            for symbol in self.crypto_symbols:
                task = asyncio.create_task(self._collect_symbol_metrics(symbol))
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Error collecting on-chain metrics: {e}")
    
    async def _collect_symbol_metrics(self, symbol: str):
        """Collect metrics for a specific symbol"""
        try:
            # Collect from multiple sources
            coinbase_data = await self._get_coinbase_metrics(symbol)
            glassnode_data = await self._get_glassnode_metrics(symbol)
            coingecko_data = await self._get_coingecko_metrics(symbol)
            
            # Combine all data
            combined_data = {
                "symbol": symbol,
                "timestamp": datetime.now(),
                "coinbase": coinbase_data,
                "glassnode": glassnode_data,
                "coingecko": coingecko_data
            }
            
            # Store data
            if symbol not in self.metrics_data:
                self.metrics_data[symbol] = []
            
            self.metrics_data[symbol].append(combined_data)
            
            # Keep only recent data
            if len(self.metrics_data[symbol]) > self.data_buffer_size:
                self.metrics_data[symbol] = self.metrics_data[symbol][-self.data_buffer_size:]
                
        except Exception as e:
            logger.error(f"Error collecting metrics for {symbol}: {e}")
    
    async def _get_coinbase_metrics(self, symbol: str) -> Dict:
        """Get metrics from Coinbase API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get price and volume data
                price_url = f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot"
                async with session.get(price_url) as response:
                    if response.status == 200:
                        price_data = await response.json()
                        return {
                            "price": float(price_data["data"]["amount"]),
                            "currency": "USD",
                            "source": "coinbase"
                        }
        except Exception as e:
            logger.error(f"Error getting Coinbase data for {symbol}: {e}")
        
        return {}
    
    async def _get_glassnode_metrics(self, symbol: str) -> Dict:
        """Get advanced on-chain metrics from Glassnode (mock implementation)"""
        try:
            # Mock implementation - in production, use actual Glassnode API
            return {
                "active_addresses": np.random.randint(500000, 2000000),
                "transaction_count": np.random.randint(200000, 800000),
                "network_hash_rate": np.random.randint(100000, 500000),
                "mvrv_ratio": np.random.uniform(0.5, 3.0),
                "nvt_ratio": np.random.uniform(10, 100),
                "realized_cap": np.random.uniform(100000000000, 1000000000000),
                "supply_in_profit": np.random.uniform(0.3, 0.9),
                "source": "glassnode"
            }
        except Exception as e:
            logger.error(f"Error getting Glassnode data for {symbol}: {e}")
            return {}
    
    async def _get_coingecko_metrics(self, symbol: str) -> Dict:
        """Get market metrics from CoinGecko API"""
        try:
            # Map symbol to CoinGecko ID
            symbol_map = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "BNB": "binancecoin",
                "ADA": "cardano",
                "SOL": "solana",
                "DOT": "polkadot",
                "MATIC": "matic-network",
                "AVAX": "avalanche-2"
            }
            
            coin_id = symbol_map.get(symbol, symbol.lower())
            
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                params = {
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "true",
                    "community_data": "false",
                    "developer_data": "false"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        market_data = data.get("market_data", {})
                        
                        return {
                            "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                            "trading_volume": market_data.get("total_volume", {}).get("usd", 0),
                            "price_change_24h": market_data.get("price_change_percentage_24h", 0),
                            "price_change_7d": market_data.get("price_change_percentage_7d", 0),
                            "price_change_30d": market_data.get("price_change_percentage_30d", 0),
                            "ath": market_data.get("ath", {}).get("usd", 0),
                            "atl": market_data.get("atl", {}).get("usd", 0),
                            "source": "coingecko"
                        }
        except Exception as e:
            logger.error(f"Error getting CoinGecko data for {symbol}: {e}")
        
        return {}
    
    def get_fear_greed_index(self) -> Dict:
        """Get Fear & Greed Index (mock implementation)"""
        try:
            # In production, use actual Fear & Greed Index API
            return {
                "value": np.random.randint(0, 100),
                "classification": np.random.choice(["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]),
                "timestamp": datetime.now(),
                "source": "alternative_me"
            }
        except Exception as e:
            logger.error(f"Error getting Fear & Greed Index: {e}")
            return {}
    
    def get_whale_activity(self, symbol: str) -> Dict:
        """Get whale activity metrics (mock implementation)"""
        try:
            return {
                "large_transactions": np.random.randint(10, 100),
                "whale_addresses": np.random.randint(100, 1000),
                "whale_balance_change": np.random.uniform(-1000000, 1000000),
                "timestamp": datetime.now(),
                "source": "whale_alert"
            }
        except Exception as e:
            logger.error(f"Error getting whale activity for {symbol}: {e}")
            return {}
    
    def get_social_sentiment(self, symbol: str) -> Dict:
        """Get social media sentiment metrics (mock implementation)"""
        try:
            return {
                "twitter_mentions": np.random.randint(1000, 10000),
                "reddit_mentions": np.random.randint(100, 1000),
                "sentiment_score": np.random.uniform(-1, 1),
                "social_volume": np.random.randint(5000, 50000),
                "timestamp": datetime.now(),
                "source": "social_media_apis"
            }
        except Exception as e:
            logger.error(f"Error getting social sentiment for {symbol}: {e}")
            return {}
    
    def calculate_onchain_features(self, symbol: str) -> Dict:
        """Calculate derived on-chain features for ML models"""
        try:
            if symbol not in self.metrics_data or len(self.metrics_data[symbol]) < 2:
                return {}
            
            recent_data = self.metrics_data[symbol][-10:]  # Last 10 data points
            
            features = {}
            
            # Price momentum features
            prices = [d.get("coinbase", {}).get("price", 0) for d in recent_data if d.get("coinbase", {}).get("price", 0) > 0]
            if len(prices) >= 2:
                features["price_momentum_1h"] = (prices[-1] - prices[-2]) / prices[-2] if prices[-2] > 0 else 0
                features["price_volatility_1h"] = np.std(prices) / np.mean(prices) if len(prices) > 1 else 0
            
            # Network activity features
            active_addresses = [d.get("glassnode", {}).get("active_addresses", 0) for d in recent_data]
            if active_addresses:
                features["active_addresses_ma"] = np.mean(active_addresses)
                features["active_addresses_trend"] = np.polyfit(range(len(active_addresses)), active_addresses, 1)[0]
            
            # Market cap features
            market_caps = [d.get("coingecko", {}).get("market_cap", 0) for d in recent_data]
            if market_caps:
                features["market_cap_ma"] = np.mean(market_caps)
                features["market_cap_trend"] = np.polyfit(range(len(market_caps)), market_caps, 1)[0]
            
            # MVRV ratio features
            mvrv_ratios = [d.get("glassnode", {}).get("mvrv_ratio", 0) for d in recent_data]
            if mvrv_ratios:
                features["mvrv_ratio_ma"] = np.mean(mvrv_ratios)
                features["mvrv_ratio_std"] = np.std(mvrv_ratios)
            
            # Supply in profit features
            supply_profit = [d.get("glassnode", {}).get("supply_in_profit", 0) for d in recent_data]
            if supply_profit:
                features["supply_profit_ma"] = np.mean(supply_profit)
                features["supply_profit_trend"] = np.polyfit(range(len(supply_profit)), supply_profit, 1)[0]
            
            return features
            
        except Exception as e:
            logger.error(f"Error calculating on-chain features: {e}")
            return {}
    
    def get_correlation_matrix(self) -> Dict:
        """Calculate correlation matrix between crypto assets"""
        try:
            symbols = list(self.metrics_data.keys())
            if len(symbols) < 2:
                return {}
            
            # Extract price data for correlation
            price_data = {}
            for symbol in symbols:
                prices = []
                for data_point in self.metrics_data[symbol][-100:]:  # Last 100 data points
                    price = data_point.get("coinbase", {}).get("price", 0)
                    if price > 0:
                        prices.append(price)
                
                if len(prices) > 10:  # Minimum data points
                    price_data[symbol] = prices
            
            if len(price_data) < 2:
                return {}
            
            # Create DataFrame and calculate correlations
            df = pd.DataFrame(price_data)
            correlation_matrix = df.corr()
            
            return {
                "correlation_matrix": correlation_matrix.to_dict(),
                "timestamp": datetime.now(),
                "symbols": list(price_data.keys())
            }
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return {}
    
    def get_market_regime_indicators(self) -> Dict:
        """Identify current market regime based on on-chain metrics"""
        try:
            regime_indicators = {}
            
            # Fear & Greed Index
            fear_greed = self.get_fear_greed_index()
            if fear_greed:
                regime_indicators["fear_greed"] = fear_greed["value"]
                regime_indicators["market_sentiment"] = fear_greed["classification"]
            
            # Volatility regime
            all_prices = []
            for symbol_data in self.metrics_data.values():
                for data_point in symbol_data[-10:]:
                    price = data_point.get("coinbase", {}).get("price", 0)
                    if price > 0:
                        all_prices.append(price)
            
            if len(all_prices) > 10:
                volatility = np.std(all_prices) / np.mean(all_prices)
                if volatility > 0.1:
                    regime_indicators["volatility_regime"] = "High"
                elif volatility > 0.05:
                    regime_indicators["volatility_regime"] = "Medium"
                else:
                    regime_indicators["volatility_regime"] = "Low"
            
            # Market cap dominance
            total_market_cap = 0
            btc_market_cap = 0
            
            for symbol, symbol_data in self.metrics_data.items():
                if symbol_data:
                    latest = symbol_data[-1]
                    market_cap = latest.get("coingecko", {}).get("market_cap", 0)
                    total_market_cap += market_cap
                    
                    if symbol == "BTC":
                        btc_market_cap = market_cap
            
            if total_market_cap > 0:
                btc_dominance = btc_market_cap / total_market_cap
                regime_indicators["btc_dominance"] = btc_dominance
                
                if btc_dominance > 0.6:
                    regime_indicators["market_structure"] = "BTC Dominant"
                elif btc_dominance > 0.4:
                    regime_indicators["market_structure"] = "Balanced"
                else:
                    regime_indicators["market_structure"] = "Altcoin Season"
            
            regime_indicators["timestamp"] = datetime.now()
            return regime_indicators
            
        except Exception as e:
            logger.error(f"Error calculating market regime indicators: {e}")
            return {}
    
    def get_latest_metrics(self, symbol: str) -> Optional[Dict]:
        """Get latest metrics for a symbol"""
        try:
            if symbol in self.metrics_data and len(self.metrics_data[symbol]) > 0:
                return self.metrics_data[symbol][-1]
            return None
        except Exception as e:
            logger.error(f"Error getting latest metrics for {symbol}: {e}")
            return None
    
    def get_metrics_history(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get historical metrics for a symbol"""
        try:
            if symbol in self.metrics_data:
                return self.metrics_data[symbol][-limit:]
            return []
        except Exception as e:
            logger.error(f"Error getting metrics history for {symbol}: {e}")
            return []
