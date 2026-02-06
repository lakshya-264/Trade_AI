"""
Sentiment Data Storage System
Time-indexed storage for sentiment analysis data with database integration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
import aiosqlite
import pandas as pd
import json
from pathlib import Path
from .enhanced_sentiment_analysis import SentimentData, SentimentSource

logger = logging.getLogger(__name__)

class SentimentDataStorage:
    """Time-indexed storage for sentiment analysis data"""
    
    def __init__(self, db_path: str = "sentiment_data.db"):
        """
        Initialize sentiment data storage
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_initialized = False
        
        # Table schemas
        self.table_schemas = {
            'sentiment_data': """
                CREATE TABLE IF NOT EXISTS sentiment_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    sentiment_score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    text TEXT,
                    metadata TEXT,
                    symbol TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            'economic_indicators': """
                CREATE TABLE IF NOT EXISTS economic_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    indicator_type TEXT NOT NULL,
                    sentiment_score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    value REAL,
                    trend TEXT,
                    summary TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            'feature_data': """
                CREATE TABLE IF NOT EXISTS feature_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    symbol TEXT NOT NULL,
                    features TEXT NOT NULL,
                    feature_names TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            'predictions': """
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    symbol TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    prediction TEXT NOT NULL,
                    probability REAL,
                    confidence REAL,
                    features_used TEXT,
                    actual_result TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            
            'aggregated_sentiment': """
                CREATE TABLE IF NOT EXISTS aggregated_sentiment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    symbol TEXT,
                    source TEXT NOT NULL,
                    period TEXT NOT NULL,  -- 'hour', 'day', 'week', 'month'
                    sentiment_mean REAL NOT NULL,
                    sentiment_std REAL NOT NULL,
                    sentiment_min REAL NOT NULL,
                    sentiment_max REAL NOT NULL,
                    volume_sum INTEGER NOT NULL,
                    data_count INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(timestamp, symbol, source, period)
                )
            """
        }
        
        logger.info(f"Sentiment storage initialized with database: {db_path}")
    
    async def initialize_database(self) -> bool:
        """Initialize database tables"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Create all tables
                for table_name, schema in self.table_schemas.items():
                    await db.execute(schema)
                
                # Create additional indexes for performance
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sentiment_composite 
                    ON sentiment_data (timestamp, source, symbol)
                """)
                
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_economic_composite 
                    ON economic_indicators (timestamp, indicator_type)
                """)
                
                await db.commit()
                self.db_initialized = True
                
                logger.info("Database initialization completed")
                return True
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
    
    async def store_sentiment_data(self, sentiment_data: List[SentimentData], 
                                 symbol: str = None) -> bool:
        """
        Store sentiment data points
        
        Args:
            sentiment_data: List of SentimentData objects
            symbol: Optional stock symbol
        
        Returns:
            Success status
        """
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            async with aiosqlite.connect(self.db_path) as db:
                for data in sentiment_data:
                    await db.execute("""
                        INSERT INTO sentiment_data 
                        (timestamp, source, sentiment_score, confidence, volume, text, metadata, symbol)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data.timestamp,
                        data.source.value if data.source else 'unknown',
                        data.sentiment_score,
                        data.confidence,
                        data.volume,
                        data.text,
                        json.dumps(data.metadata),
                        symbol
                    ))
                
                await db.commit()
                logger.info(f"Stored {len(sentiment_data)} sentiment data points")
                return True
                
        except Exception as e:
            logger.error(f"Error storing sentiment data: {e}")
            return False
    
    async def store_economic_indicators(self, economic_data: Dict[str, SentimentData]) -> bool:
        """
        Store economic indicators data
        
        Args:
            economic_data: Dictionary of economic indicators
        
        Returns:
            Success status
        """
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            async with aiosqlite.connect(self.db_path) as db:
                for indicator_type, data in economic_data.items():
                    await db.execute("""
                        INSERT INTO economic_indicators 
                        (timestamp, indicator_type, sentiment_score, confidence, value, trend, summary, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data.timestamp,
                        indicator_type,
                        data.sentiment_score,
                        data.confidence,
                        data.metadata.get('value'),
                        data.metadata.get('trend'),
                        data.text,
                        json.dumps(data.metadata)
                    ))
                
                await db.commit()
                logger.info(f"Stored {len(economic_data)} economic indicators")
                return True
                
        except Exception as e:
            logger.error(f"Error storing economic indicators: {e}")
            return False
    
    async def store_feature_data(self, features_df: pd.DataFrame, symbol: str) -> bool:
        """
        Store engineered features
        
        Args:
            features_df: DataFrame with features
            symbol: Stock symbol
        
        Returns:
            Success status
        """
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            async with aiosqlite.connect(self.db_path) as db:
                for _, row in features_df.iterrows():
                    # Extract features (exclude timestamp)
                    feature_dict = row.drop('timestamp', errors='ignore').to_dict()
                    feature_names = list(feature_dict.keys())
                    feature_values = list(feature_dict.values())
                    
                    await db.execute("""
                        INSERT INTO feature_data 
                        (timestamp, symbol, features, feature_names)
                        VALUES (?, ?, ?, ?)
                    """, (
                        row.get('timestamp', datetime.utcnow()),
                        symbol,
                        json.dumps(feature_values),
                        json.dumps(feature_names)
                    ))
                
                await db.commit()
                logger.info(f"Stored {len(features_df)} feature records")
                return True
                
        except Exception as e:
            logger.error(f"Error storing feature data: {e}")
            return False
    
    async def store_prediction(self, prediction_data: Dict[str, Any]) -> bool:
        """
        Store model prediction
        
        Args:
            prediction_data: Dictionary with prediction details
        
        Returns:
            Success status
        """
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO predictions 
                    (timestamp, symbol, model_type, prediction, probability, confidence, features_used, actual_result)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prediction_data.get('timestamp', datetime.utcnow()),
                    prediction_data.get('symbol'),
                    prediction_data.get('model_type'),
                    prediction_data.get('prediction'),
                    prediction_data.get('probability'),
                    prediction_data.get('confidence'),
                    json.dumps(prediction_data.get('features_used', [])),
                    prediction_data.get('actual_result')
                ))
                
                await db.commit()
                logger.info(f"Stored prediction for {prediction_data.get('symbol')}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
            return False
    
    async def get_sentiment_data(self, start_time: datetime = None, 
                              end_time: datetime = None,
                              source: str = None,
                              symbol: str = None,
                              limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieve sentiment data with filters
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            source: Source filter
            symbol: Symbol filter
            limit: Maximum records to return
        
        Returns:
            List of sentiment data records
        """
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            query = "SELECT * FROM sentiment_data WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error retrieving sentiment data: {e}")
            return []
    
    async def get_aggregated_sentiment(self, period: str = 'day',
                                     symbol: str = None,
                                     start_time: datetime = None,
                                     end_time: datetime = None) -> List[Dict[str, Any]]:
        """
        Get aggregated sentiment data
        
        Args:
            period: Aggregation period ('hour', 'day', 'week', 'month')
            symbol: Symbol filter
            start_time: Start time filter
            end_time: End time filter
        
        Returns:
            List of aggregated sentiment records
        """
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            query = "SELECT * FROM aggregated_sentiment WHERE period = ?"
            params = [period]
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC"
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error retrieving aggregated sentiment: {e}")
            return []
    
    async def aggregate_sentiment_data(self, period: str = 'day',
                                     start_time: datetime = None,
                                     end_time: datetime = None) -> bool:
        """
        Aggregate sentiment data by time period
        
        Args:
            period: Aggregation period
            start_time: Start time for aggregation
            end_time: End time for aggregation
        
        Returns:
            Success status
        """
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            # Default to last 30 days if no time range specified
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(days=30)
            
            # Get raw sentiment data for the period
            raw_data = await self.get_sentiment_data(start_time, end_time, limit=10000)
            
            if not raw_data:
                logger.info("No data to aggregate")
                return True
            
            # Group by time period, source, and symbol
            aggregated = {}
            
            for record in raw_data:
                timestamp = datetime.fromisoformat(record['timestamp'])
                
                # Determine aggregation bucket
                if period == 'hour':
                    bucket = timestamp.replace(minute=0, second=0, microsecond=0)
                elif period == 'day':
                    bucket = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                elif period == 'week':
                    # Start of week (Monday)
                    days_since_monday = timestamp.weekday()
                    bucket = (timestamp - timedelta(days=days_since_monday)).replace(
                        hour=0, minute=0, second=0, microsecond=0)
                elif period == 'month':
                    bucket = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                else:
                    bucket = timestamp  # No aggregation
                
                key = (bucket, record['source'], record.get('symbol'))
                
                if key not in aggregated:
                    aggregated[key] = {
                        'sentiments': [],
                        'volumes': [],
                        'count': 0
                    }
                
                aggregated[key]['sentiments'].append(record['sentiment_score'])
                aggregated[key]['volumes'].append(record['volume'])
                aggregated[key]['count'] += 1
            
            # Store aggregated data
            async with aiosqlite.connect(self.db_path) as db:
                for (timestamp, source, symbol), data in aggregated.items():
                    sentiments = data['sentiments']
                    volumes = data['volumes']
                    
                    await db.execute("""
                        INSERT OR REPLACE INTO aggregated_sentiment 
                        (timestamp, symbol, source, period, sentiment_mean, sentiment_std, 
                         sentiment_min, sentiment_max, volume_sum, data_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp,
                        symbol,
                        source,
                        period,
                        sum(sentiments) / len(sentiments),
                        pd.Series(sentiments).std(),
                        min(sentiments),
                        max(sentiments),
                        sum(volumes),
                        len(sentiments)
                    ))
                
                await db.commit()
                logger.info(f"Aggregated {len(aggregated)} records for period: {period}")
                return True
                
        except Exception as e:
            logger.error(f"Error aggregating sentiment data: {e}")
            return False
    
    async def get_feature_data(self, symbol: str = None,
                            start_time: datetime = None,
                            end_time: datetime = None,
                            limit: int = 1000) -> pd.DataFrame:
        """
        Retrieve feature data as DataFrame
        
        Args:
            symbol: Symbol filter
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum records
        
        Returns:
            DataFrame with feature data
        """
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            query = "SELECT * FROM feature_data WHERE 1=1"
            params = []
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                # Convert to DataFrame
                data = []
                for row in rows:
                    feature_values = json.loads(row[3]) if row[3] else []
                    feature_names = json.loads(row[4]) if row[4] else []
                    
                    row_dict = {
                        'timestamp': row[1],
                        'symbol': row[2]
                    }
                    
                    # Add features
                    for i, name in enumerate(feature_names):
                        if i < len(feature_values):
                            row_dict[name] = feature_values[i]
                    
                    data.append(row_dict)
                
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"Error retrieving feature data: {e}")
            return pd.DataFrame()
    
    async def get_predictions(self, symbol: str = None,
                            model_type: str = None,
                            start_time: datetime = None,
                            end_time: datetime = None,
                            limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieve model predictions
        
        Args:
            symbol: Symbol filter
            model_type: Model type filter
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum records
        
        Returns:
            List of prediction records
        """
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            query = "SELECT * FROM predictions WHERE 1=1"
            params = []
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if model_type:
                query += " AND model_type = ?"
                params.append(model_type)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error retrieving predictions: {e}")
            return []
    
    async def cleanup_old_data(self, retention_days: int = 90) -> bool:
        """
        Clean up old data beyond retention period
        
        Args:
            retention_days: Number of days to retain data
        
        Returns:
            Success status
        """
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            async with aiosqlite.connect(self.db_path) as db:
                # Clean up raw sentiment data
                cursor1 = await db.execute(
                    "DELETE FROM sentiment_data WHERE timestamp < ?", (cutoff_date,)
                )
                sentiment_deleted = cursor1.rowcount
                
                # Clean up feature data
                cursor2 = await db.execute(
                    "DELETE FROM feature_data WHERE timestamp < ?", (cutoff_date,)
                )
                features_deleted = cursor2.rowcount
                
                # Keep aggregated data longer (1 year)
                aggregated_cutoff = datetime.utcnow() - timedelta(days=365)
                cursor3 = await db.execute(
                    "DELETE FROM aggregated_sentiment WHERE timestamp < ?", (aggregated_cutoff,)
                )
                aggregated_deleted = cursor3.rowcount
                
                await db.commit()
                
                logger.info(f"Cleanup completed: {sentiment_deleted} sentiment records, "
                          f"{features_deleted} feature records, {aggregated_deleted} aggregated records")
                return True
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return False
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            stats = {}
            
            async with aiosqlite.connect(self.db_path) as db:
                # Get table sizes
                tables = ['sentiment_data', 'economic_indicators', 'feature_data', 
                         'predictions', 'aggregated_sentiment']
                
                for table in tables:
                    cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                    count = (await cursor.fetchone())[0]
                    stats[f"{table}_count"] = count
                
                # Get date ranges
                cursor = await db.execute("""
                    SELECT MIN(timestamp), MAX(timestamp) FROM sentiment_data
                """)
                min_date, max_date = await cursor.fetchone()
                stats['date_range'] = {
                    'earliest': min_date,
                    'latest': max_date
                }
                
                # Get database file size
                db_path = Path(self.db_path)
                if db_path.exists():
                    stats['file_size_mb'] = db_path.stat().st_size / (1024 * 1024)
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return stats
    
    async def _get_table_list(self) -> List[str]:
        """Get list of tables in the database"""
        try:
            if not self.db_initialized:
                await self.initialize_database()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in await cursor.fetchall()]
                return tables
                
        except Exception as e:
            logger.error(f"Error getting table list: {e}")
            return []
    
    async def export_data(self, output_path: str, 
                         start_time: datetime = None,
                         end_time: datetime = None) -> bool:
        """
        Export data to CSV files
        
        Args:
            output_path: Directory to export files
            start_time: Start time filter
            end_time: End time filter
        
        Returns:
            Success status
        """
        try:
            output_dir = Path(output_path)
            output_dir.mkdir(exist_ok=True)
            
            # Export sentiment data
            sentiment_data = await self.get_sentiment_data(start_time, end_time, limit=10000)
            if sentiment_data:
                df_sentiment = pd.DataFrame(sentiment_data)
                df_sentiment.to_csv(output_dir / "sentiment_data.csv", index=False)
            
            # Export economic indicators
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                query = "SELECT * FROM economic_indicators WHERE 1=1"
                params = []
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time)
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time)
                
                cursor = await db.execute(query, params)
                economic_data = [dict(row) for row in await cursor.fetchall()]
                
                if economic_data:
                    df_economic = pd.DataFrame(economic_data)
                    df_economic.to_csv(output_dir / "economic_indicators.csv", index=False)
            
            # Export aggregated sentiment
            agg_data = await self.get_aggregated_sentiment('day', start_time=start_time, end_time=end_time)
            if agg_data:
                df_agg = pd.DataFrame(agg_data)
                df_agg.to_csv(output_dir / "aggregated_sentiment.csv", index=False)
            
            logger.info(f"Data exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False

# Factory function
async def create_sentiment_storage(db_path: str = "sentiment_data.db") -> SentimentDataStorage:
    """Create and initialize sentiment data storage"""
    storage = SentimentDataStorage(db_path)
    await storage.initialize_database()
    return storage
