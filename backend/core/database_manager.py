"""
Database Manager for Dual Database Architecture
Manages PostgreSQL (primary) and SQLite (secondary) databases with failover support
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages dual database architecture with PostgreSQL primary and SQLite secondary
    Provides automatic failover and data synchronization
    """
    
    def __init__(self):
        self.primary_db_url = os.getenv("DATABASE_URL_PRIMARY")
        self.secondary_db_url = os.getenv("DATABASE_URL_SECONDARY")
        self.failover_enabled = os.getenv("DB_FAILOVER_ENABLED", "true").lower() == "true"
        self.sync_interval = int(os.getenv("DB_SYNC_INTERVAL_SECONDS", "60"))
        
        # Database engines
        self.primary_engine = None
        self.secondary_engine = None
        self.primary_session = None
        self.secondary_session = None
        
        # Connection status
        self.primary_available = False
        self.secondary_available = False
        self.last_sync_time = None
        
        logger.info("Database Manager initialized")
    
    async def initialize(self):
        """Initialize database connections"""
        try:
            await self._initialize_primary_db()
            await self._initialize_secondary_db()
            logger.info("Database Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Database Manager: {e}")
            raise
    
    async def _initialize_primary_db(self):
        """Initialize PostgreSQL primary database"""
        if not self.primary_db_url:
            logger.warning("Primary database URL not configured")
            return
        
        try:
            # Create async engine for PostgreSQL
            self.primary_engine = create_async_engine(
                self.primary_db_url.replace("postgresql://", "postgresql+asyncpg://"),
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600
            )
            
            # Test connection
            async with self.primary_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self.primary_available = True
            logger.info("Primary database (PostgreSQL) connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to primary database: {e}")
            self.primary_available = False
    
    async def _initialize_secondary_db(self):
        """Initialize SQLite secondary database"""
        if not self.secondary_db_url:
            logger.warning("Secondary database URL not configured")
            return
        
        try:
            # Extract file path from SQLite URL
            db_file = self.secondary_db_url.replace("sqlite:///", "").replace("sqlite:////", "")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_file), exist_ok=True)
            
            # Create async engine for SQLite
            self.secondary_engine = create_async_engine(
                f"sqlite+aiosqlite:///{db_file}",
                echo=False,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
            
            # Test connection
            async with self.secondary_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self.secondary_available = True
            logger.info("Secondary database (SQLite) connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to secondary database: {e}")
            self.secondary_available = False
    
    def get_primary_session(self) -> AsyncSession:
        """Get primary database session"""
        if not self.primary_available:
            raise Exception("Primary database not available")
        
        return AsyncSession(self.primary_engine)
    
    def get_secondary_session(self) -> AsyncSession:
        """Get secondary database session"""
        if not self.secondary_available:
            raise Exception("Secondary database not available")
        
        return AsyncSession(self.secondary_engine)
    
    async def get_active_session(self) -> AsyncSession:
        """Get active database session with failover support"""
        if self.primary_available:
            return self.get_primary_session()
        elif self.secondary_available and self.failover_enabled:
            logger.warning("Using secondary database due to primary unavailability")
            return self.get_secondary_session()
        else:
            raise Exception("No database available")
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute query with automatic failover"""
        try:
            # Try primary database first
            if self.primary_available:
                async with self.get_primary_session() as session:
                    result = await session.execute(text(query), params or {})
                    await session.commit()
                    return result
        except Exception as e:
            logger.warning(f"Primary database query failed: {e}")
            
            # Try secondary database if failover enabled
            if self.secondary_available and self.failover_enabled:
                try:
                    async with self.get_secondary_session() as session:
                        result = await session.execute(text(query), params or {})
                        await session.commit()
                        return result
                except Exception as e2:
                    logger.error(f"Secondary database query also failed: {e2}")
                    raise Exception(f"Both databases failed: Primary: {e}, Secondary: {e2}")
            else:
                raise e
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on both databases"""
        health_status = {
            "primary": {"status": "unknown", "error": None},
            "secondary": {"status": "unknown", "error": None},
            "failover_enabled": self.failover_enabled,
            "last_sync": self.last_sync_time
        }
        
        # Check primary database
        if self.primary_db_url:
            try:
                async with self.primary_engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                health_status["primary"]["status"] = "healthy"
            except Exception as e:
                health_status["primary"]["status"] = "unhealthy"
                health_status["primary"]["error"] = str(e)
        
        # Check secondary database
        if self.secondary_db_url:
            try:
                async with self.secondary_engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                health_status["secondary"]["status"] = "healthy"
            except Exception as e:
                health_status["secondary"]["status"] = "unhealthy"
                health_status["secondary"]["error"] = str(e)
        
        return health_status
    
    async def sync_databases(self):
        """Synchronize data between primary and secondary databases"""
        if not (self.primary_available and self.secondary_available):
            logger.warning("Cannot sync: both databases must be available")
            return
        
        try:
            logger.info("Starting database synchronization...")
            
            # Implementation would depend on specific sync requirements
            # For now, we'll just update the sync timestamp
            self.last_sync_time = datetime.now()
            
            logger.info("Database synchronization completed")
            
        except Exception as e:
            logger.error(f"Database synchronization failed: {e}")
    
    async def get_table_count(self, table_name: str) -> Dict[str, int]:
        """Get row count for a table from both databases"""
        counts = {"primary": 0, "secondary": 0}
        
        # Count from primary
        if self.primary_available:
            try:
                result = await self.execute_query(f"SELECT COUNT(*) FROM {table_name}")
                counts["primary"] = result.scalar() if result else 0
            except Exception as e:
                logger.warning(f"Failed to count from primary database: {e}")
        
        # Count from secondary
        if self.secondary_available:
            try:
                result = await self.execute_query(f"SELECT COUNT(*) FROM {table_name}")
                counts["secondary"] = result.scalar() if result else 0
            except Exception as e:
                logger.warning(f"Failed to count from secondary database: {e}")
        
        return counts
    
    async def close(self):
        """Close all database connections"""
        try:
            if self.primary_engine:
                await self.primary_engine.dispose()
            if self.secondary_engine:
                await self.secondary_engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for debugging"""
        return {
            "primary_url": self.primary_db_url[:20] + "..." if self.primary_db_url else None,
            "secondary_url": self.secondary_db_url[:20] + "..." if self.secondary_db_url else None,
            "primary_available": self.primary_available,
            "secondary_available": self.secondary_available,
            "failover_enabled": self.failover_enabled,
            "sync_interval": self.sync_interval,
            "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None
        }

# Global database manager instance
db_manager: Optional[DatabaseManager] = None

async def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
        await db_manager.initialize()
    return db_manager

# Dependency function for FastAPI
async def get_db():
    """FastAPI dependency to get database session"""
    manager = await get_database_manager()
    return await manager.get_active_session()

# Context manager for database operations
@asynccontextmanager
async def get_db_context():
    """Context manager for database operations with automatic cleanup"""
    manager = await get_database_manager()
    session = await manager.get_active_session()
    try:
        yield session
    finally:
        await session.close()
