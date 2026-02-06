"""
Database Migration: Add Advanced Features Tables
Adds tables for social trading, advanced orders, analytics, etc.
"""

import logging
from sqlalchemy import text
from core.database_unified import engine, Base

logger = logging.getLogger(__name__)

def add_advanced_features_tables():
    """Add tables for advanced features"""
    try:
        with engine.connect() as conn:
            # Social Trading Tables
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS trading_ideas (
                    id VARCHAR PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    symbol VARCHAR NOT NULL,
                    analysis TEXT NOT NULL,
                    chart_snapshot TEXT,
                    tags VARCHAR,
                    likes INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS trader_follows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    follower_id INTEGER NOT NULL,
                    trader_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(follower_id, trader_id),
                    FOREIGN KEY (follower_id) REFERENCES users(id),
                    FOREIGN KEY (trader_id) REFERENCES users(id)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS idea_comments (
                    id VARCHAR PRIMARY KEY,
                    idea_id VARCHAR NOT NULL,
                    user_id INTEGER NOT NULL,
                    comment TEXT NOT NULL,
                    likes INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (idea_id) REFERENCES trading_ideas(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS copied_strategies (
                    id VARCHAR PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    trader_id INTEGER NOT NULL,
                    strategy_id VARCHAR NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (trader_id) REFERENCES users(id)
                )
            """))
            
            # Advanced Order Management Tables
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS bracket_orders (
                    id VARCHAR PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    symbol VARCHAR NOT NULL,
                    side VARCHAR NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    target REAL NOT NULL,
                    status VARCHAR DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS oco_orders (
                    id VARCHAR PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    symbol VARCHAR NOT NULL,
                    side VARCHAR NOT NULL,
                    quantity INTEGER NOT NULL,
                    price1 REAL NOT NULL,
                    price2 REAL NOT NULL,
                    status VARCHAR DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS trade_journal (
                    id VARCHAR PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    symbol VARCHAR NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    side VARCHAR NOT NULL,
                    pnl REAL,
                    pnl_percent REAL,
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            
            # Analytics Tables
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS analysis_accuracy (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id VARCHAR NOT NULL,
                    symbol VARCHAR NOT NULL,
                    predicted_price REAL NOT NULL,
                    predicted_direction VARCHAR NOT NULL,
                    actual_price REAL,
                    actual_direction VARCHAR,
                    accuracy TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            conn.commit()
            logger.info("✅ Advanced features tables created successfully")
            
    except Exception as e:
        logger.error(f"Error creating advanced features tables: {e}")
        raise

if __name__ == "__main__":
    add_advanced_features_tables()

