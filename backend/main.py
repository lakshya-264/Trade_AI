"""
Main FastAPI application for Trader AI
Indian Stock Market Trading Platform
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import uvicorn
import os
import json
import logging
from datetime import datetime, timedelta
import asyncio
from dotenv import load_dotenv, find_dotenv
import warnings
from sqlalchemy.orm import Session

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional: Filter overly chatty access logs for specific paths
class AccessPathFilter(logging.Filter):
    def __init__(self, ignored_substrings: list[str]):
        super().__init__()
        self.ignored_substrings = ignored_substrings

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True
        return not any(substr in message for substr in self.ignored_substrings)

# Apply filter to uvicorn access logger (keeps other access logs)
try:
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.addFilter(AccessPathFilter([
        "/api/trading/portfolio",  # noisy polling endpoint
        # "/api/realtime/market/summary",  # add more if needed
        # "/api/realtime/market-status",
    ]))
except Exception:
    pass

# Reduce noisy asyncio transport errors (temporary suppression)
try:
    # Silence generic asyncio logger to critical only
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)

    class SubstringFilter(logging.Filter):
        def __init__(self, substrings: list[str]):
            super().__init__()
            self.substrings = substrings
        def filter(self, record: logging.LogRecord) -> bool:
            try:
                msg = record.getMessage()
            except Exception:
                return True
            return not any(s in msg for s in self.substrings)

    noisy_substrings = [
        "_ProactorBasePipeTransport._call_connection_lost",
        "Exception in callback _ProactorBasePipeTransport",
    ]
    logging.getLogger("uvicorn.error").addFilter(SubstringFilter(noisy_substrings))
    logging.getLogger("asyncio").addFilter(SubstringFilter(noisy_substrings))
except Exception:
    pass

# Reduce info-level chatter from specific app loggers (keep warnings/errors)
try:
    logging.getLogger("core.yahoo_finance_scraper").setLevel(logging.WARNING)
    logging.getLogger("core.intelligent_fallback_system").setLevel(logging.WARNING)
    logging.getLogger("core.data_service").setLevel(logging.WARNING)
except Exception:
    pass

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.security import create_secure_app, check_rate_limit

# Import request filter middleware
# from middleware.request_filter import RequestFilterMiddleware

# Load environment variables (support .env in project root)
# First try current working dir, then search upwards
try:
    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path)
    else:
        load_dotenv()
except Exception:
    load_dotenv()

# Import routers
from api.routes import (
    social_trading_routes,
    advanced_orders_routes,
    analytics_routes,
    realtime,
    trading,
    unified_ai,
    risk,
    monitoring,
    auth,
    sessions,  # Session management
    chat,
    education,
    intelligent_trading,
    # arpit_education,  # Commented out - keeping for future use
    portfolio_allocation,
    charting,
    enhanced_charting,  # Enhanced charting with alerts and watchlists
    comprehensive_trading,  # New comprehensive trading routes
    stocks,  # NSE & BSE stock list routes
    # upstox_auth,  # Upstox API integration - REMOVED
    candle_data,  # Candlestick data API
    trendlines,  # Auto trendline detection
    swing_points,  # Swing point analysis (HH/HL/LH/LL)
    market_structure,  # Market Structure (BOS/CHoCH)
    support_resistance,  # Support & Resistance levels
    supply_demand,  # Supply & Demand zones
    multi_timeframe,  # Multi-timeframe analysis (Phase 3)
    alerts,  # Alert System (Phase 4)
    backtesting,  # Backtesting Engine (Phase 5)
    screener,  # Stock Screener
    financial_data,  # Financial data and ratios
    market_factors,  # Market factors (FII/DII, etc.)
    paper_trading,  # Paper Trading (Virtual Accounts)
)
from api.routes import ml_training  # ML Training endpoints
from api.routes import model_training  # Model Training & Performance Monitoring
from api.routes import market_education  # Market Education (IPO, CPR, Regulators, etc.)
from api.routes import sync_jobs  # Sync jobs
from api.routes import user_learning  # User Learning & Feedback
from api.routes import advanced_learning  # Advanced Learning (Retraining, Feature Selection, etc.)
from api.routes import social_trading_routes  # Social Trading
from api.routes import advanced_orders_routes  # Advanced Orders
from api.routes import analytics_routes  # Analytics
from api.trading_performance import router as trading_performance_router  # Trading Performance endpoints
from api.nifty50_trading_performance import router as nifty50_performance_router  # Nifty50 Performance endpoints
from api.simple_portfolio import router as simple_portfolio_router  # Simple Portfolio endpoints
from api.order_book import router as order_book_router  # Order Book endpoints
from api.holdings import router as holdings_router  # Holdings endpoints
from api.realtime_trading import router as realtime_trading_router  # Real-time Trading endpoints
from api.routes import market as market_routes
from api.routes import market_dashboard
from api.routes import consolidated_analysis  # Consolidated Analysis
from core.database import engine, Base, SessionLocal, MarketData, get_db
from core.database_unified import engine as unified_engine, Base as UnifiedBase, Portfolio, PortfolioMetadata, User
from models.trading_performance_models import TradingExecution
from core.auth_dependencies import get_current_active_user
from core.websocket_manager import WebSocketManager
from core.data_service import data_service

# Import Strategy models to ensure tables are created
try:
    from models.strategy import Strategy, PaperTrade
except ImportError:
    try:
        from backend.models.strategy import Strategy, PaperTrade
    except ImportError:
        pass  # Models will be imported when needed

# Get default user credentials from environment
import os
DEFAULT_USER = os.getenv("DEFAULT_USER", "tester2")
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "password123")

# Startup
logger.info("🚀 Starting Trader AI Backend...")

# Start the broadcast scheduler when the module is imported
async def start_websocket_scheduler():
    """Start the WebSocket broadcast scheduler"""
    asyncio.create_task(manager.start_broadcast_scheduler())
    
    # Start real-time broadcasting
    from services.realtime_websocket_broadcaster import broadcaster
    await broadcaster.start_broadcasting()

# Simple startup without async context manager
def start_background_tasks():
    """Start all background tasks"""
    try:
        # Market data collection - temporarily disabled due to import issue
        # asyncio.create_task(market_data_service.start_data_collection())
        
        # Cleanup tasks - temporarily disabled due to import issue
        # asyncio.create_task(cleanup_service.start_cleanup_tasks())
        
        # Daily financial data sync - temporarily disabled due to import issue
        # asyncio.create_task(financial_data_service.start_daily_sync())
        
        # Limit order monitoring - temporarily disabled
        # asyncio.create_task(_start_limit_order_monitoring())
        
        # Auto-trading execution - starts after 2 minutes delay
        asyncio.create_task(auto_execute_nifty50_trades())
        
        logger.info("✅ Background tasks started (auto-trading enabled)")
        
    except Exception as e:
        logger.error(f"Error starting background tasks: {e}")

async def auto_execute_nifty50_trades():
    """Auto-execute Nifty 50 trades on server startup"""
    import asyncio
    from datetime import datetime
    
    # Wait 2 minutes for server to fully start
    await asyncio.sleep(120)
    
    try:
        logger.info("🤖 Starting auto-execution of Nifty 50 trades...")
        
        # Import the realtime trading module
        from api.realtime_trading import execute_nifty50_signals
        from core.auth_dependencies import get_current_user
        
        # Get the default user ID for auto-execution
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine, text
        
        database_url = "sqlite:///D:/Trader_AI_WEB_V_0.3/Trader_AI_V_0.1/trader_ai.db"
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            user_result = session.execute(text("""
                SELECT id FROM users WHERE username = :username
            """), {'username': DEFAULT_USER}).fetchone()
            
            if user_result:
                user_id = user_result[0]
                mock_user = type('User', (), {'id': user_id, 'username': DEFAULT_USER})()
                logger.info(f"🤖 Using user '{DEFAULT_USER}' (ID: {user_id}) for auto-execution")
            else:
                logger.error(f"❌ Default user '{DEFAULT_USER}' not found for auto-execution")
                return
                
        except Exception as e:
            logger.error(f"❌ Error getting user for auto-execution: {e}")
            return
        finally:
            session.close()
        
        # Execute trades with paper trading mode for safety
        result = await execute_nifty50_signals(
            timeframe="5m",
            max_trades=3,  # Conservative: only 3 trades
            min_confidence=0.8,  # High confidence only
            paper_trading=True,  # Paper trading for safety
            current_user=mock_user
        )
        
        if result.get('success'):
            executed_count = len(result.get('executed_trades', []))
            logger.info(f"✅ Auto-executed {executed_count} Nifty 50 trades successfully")
            logger.info(f"📊 Portfolio updated: {result.get('portfolio_update', {})}")
        else:
            logger.error(f"❌ Auto-execution failed: {result.get('error')}")
        
        # Update auto-trading status
        from api.routes.auto_trading_status import update_auto_trading_status
        update_auto_trading_status(result.get('success', False), result)
            
    except Exception as e:
        logger.error(f"❌ Error in auto-execution: {e}")
        
    # Schedule next execution in 30 minutes
    await asyncio.sleep(1800)  # 30 minutes
    # Recursively call for continuous execution
    asyncio.create_task(auto_execute_nifty50_trades())

# Start background tasks
start_background_tasks()

# Create database tables
# Create all database tables
Base.metadata.create_all(bind=engine)
# Also create unified database tables (including UserSession)
try:
    UnifiedBase.metadata.create_all(bind=engine)  # Use same engine
    logger.info("✅ Unified database tables created (including UserSession)")
except Exception as e:
    logger.warning(f"⚠️ Could not create unified tables: {e}")

# Use default user credentials from environment (defined above)
default_username = DEFAULT_USER
default_password = DEFAULT_PASSWORD

# Create default user if not exists
try:
    from core.database_unified import User
    from core.security import get_password_hash
    import os
    from datetime import datetime
    
    # Use direct database connection for user creation
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine, text
    
    database_url = "sqlite:///D:/Trader_AI_WEB_V_0.3/Trader_AI_V_0.1/trader_ai.db"
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if user already exists
        existing_user = session.execute(text("""
            SELECT id FROM users WHERE username = :username
        """), {'username': DEFAULT_USER}).fetchone()
        
        if not existing_user:
            # Create default user
            hashed_password = get_password_hash(DEFAULT_PASSWORD)
            session.execute(text("""
                INSERT INTO users (username, email, hashed_password, is_active, created_at)
                VALUES (:username, :email, :hashed_password, :is_active, :created_at)
            """), {
                'username': DEFAULT_USER,
                'email': f"{DEFAULT_USER}@traderai.com",
                'hashed_password': hashed_password,
                'is_active': True,
                'created_at': datetime.utcnow()
            })
            
            session.commit()
            logger.info(f"✅ Created default user: {DEFAULT_USER}")
        else:
            logger.info(f"ℹ️ Default user '{DEFAULT_USER}' already exists")
            
    except Exception as user_error:
        session.rollback()
        logger.error(f"❌ Error creating default user: {user_error}")
    finally:
        session.close()
        
except Exception as e:
    logger.error(f"❌ Error in user creation setup: {e}")

# Create secure FastAPI app
app = create_secure_app()

# CORS middleware for AWS deployment
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
cors_credentials = os.getenv("CORS_CREDENTIALS", "true").lower() == "true"
cors_methods_env = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS,PATCH")
cors_methods = [method.strip() for method in cors_methods_env.split(",") if method.strip()]
cors_headers_env = os.getenv("CORS_HEADERS", "*")
cors_headers = [header.strip() for header in cors_headers_env.split(",") if header.strip()] if cors_headers_env != "*" else ["*"]

# Add CORS middleware - must be added before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],  # Fallback to allow all if empty
    allow_credentials=cors_credentials,
    allow_methods=cors_methods if "OPTIONS" in cors_methods else cors_methods + ["OPTIONS"],  # Ensure OPTIONS is included
    allow_headers=cors_headers,
    expose_headers=["*"],  # Expose all headers
    max_age=3600,  # Cache preflight requests for 1 hour
)

logger.info(f"✅ CORS configured: Origins={allowed_origins[:3]}..., Methods={cors_methods}, Credentials={cors_credentials}")

# Add request filter middleware to handle unknown requests
# app.add_middleware(RequestFilterMiddleware)

# Explicit OPTIONS handler for CORS preflight (fallback) - must be before catch-all route
@app.options("/api/{full_path:path}")
async def options_api_handler(full_path: str):
    """Handle OPTIONS requests for API routes (CORS preflight)"""
    from fastapi.responses import Response
    origin = "*"  # Allow all origins for OPTIONS
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
    )

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle OPTIONS requests for all other routes (CORS preflight)"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        }
    )

# WebSocket manager
websocket_manager = WebSocketManager()

# ----------------------------
# Background tasks configuration
# ----------------------------
# Nifty 50 stocks
NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK", "HDFC", "ITC", "BHARTIARTL",
    "SBIN", "BAJFINANCE", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "POWERGRID",
    "NTPC", "TECHM", "WIPRO", "HCLTECH", "LT", "BAJAJFINSV", "DRREDDY", "TATAMOTORS", "BRITANNIA", "EICHERMOT",
    "SHREECEM", "JSWSTEEL", "TATASTEEL", "INDUSINDBK", "COALINDIA", "GRASIM", "CIPLA", "ONGC", "TATACONSUM", "APOLLOHOSP",
    "ADANIPORTS", "BPCL", "HEROMOTOCO", "DIVISLAB", "UPL", "BAJAJ-AUTO", "TATAPOWER", "ADANIENT", "SBILIFE", "HINDALCO"
]

TRACKED_SYMBOLS = [s.strip() for s in os.getenv("TRACKED_SYMBOLS", ",".join(NIFTY_50_SYMBOLS)).split(",") if s.strip()]
FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", "30"))  # Increased for 50 stocks
CLEANUP_RETENTION_DAYS = int(os.getenv("CLEANUP_RETENTION_DAYS", "7"))

async def fetch_and_broadcast_loop():
    """Periodic task: fetch quotes, persist to DB, and broadcast via WebSocket."""
    # Wait a bit before starting to allow server to fully initialize
    await asyncio.sleep(5)
    
    while True:
        try:
            for symbol in TRACKED_SYMBOLS:
                try:
                    quote = await data_service.get_quote(symbol, exchange="NSE")
                except Exception as e:
                    logger.warning(f"Failed to fetch quote for {symbol}: {e}")
                    quote = None
                if not quote or "last_price" not in quote:
                    continue

                # Persist to database
                session = SessionLocal()
                try:
                    market_data = MarketData(
                        symbol=symbol,
                        exchange="NSE",
                        last_price=float(quote.get("last_price", 0.0)),
                        change=float(quote.get("change", 0.0)),
                        change_percent=float(quote.get("change_percent", 0.0)),
                        volume=int(quote.get("volume", 0)),
                        open_price=float(quote.get("open", 0.0)) if "open" in quote else None,
                        high_price=float(quote.get("high", 0.0)) if "high" in quote else None,
                        low_price=float(quote.get("low", 0.0)) if "low" in quote else None,
                        close_price=float(quote.get("close", 0.0)) if "close" in quote else None,
                        timestamp=datetime.utcnow()
                    )
                    session.add(market_data)
                    session.commit()
                except Exception:
                    session.rollback()
                finally:
                    session.close()

                # Broadcast to subscribers
                try:
                    await websocket_manager.send_to_subscribers(symbol, quote)
                except Exception:
                    pass

        except Exception:
            # Avoid crashing the loop; sleep and continue
            await asyncio.sleep(FETCH_INTERVAL_SECONDS)
        await asyncio.sleep(FETCH_INTERVAL_SECONDS)

async def cleanup_loop():
    """Periodic cleanup of old MarketData records."""
    while True:
        try:
            cutoff = datetime.utcnow() - timedelta(days=CLEANUP_RETENTION_DAYS)
            session = SessionLocal()
            try:
                # SQLite compatible deletion
                session.query(MarketData).filter(MarketData.timestamp < cutoff).delete(synchronize_session=False)
                session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()
        except Exception:
            pass
        # Run cleanup every hour
        await asyncio.sleep(3600)

async def daily_financial_sync_loop():
    """Daily sync of financial data for all Nifty 50 stocks."""
    # Wait for server to fully initialize
    await asyncio.sleep(30)
    
    # Calculate seconds until next 2 AM IST (8:30 PM UTC / 2:00 AM IST)
    # Or run immediately on first start, then daily
    first_run = True
    
    while True:
        try:
            if first_run:
                # Run immediately on first start
                logger.info("🔄 Running initial daily financial data sync...")
                first_run = False
            else:
                # Wait until next day at 2 AM IST (8:30 PM UTC previous day)
                now = datetime.utcnow()
                # Target: 8:30 PM UTC (2:00 AM IST next day)
                target_hour = 20  # 8 PM UTC
                target_minute = 30
                
                target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                if target_time <= now:
                    # If target time has passed today, schedule for tomorrow
                    target_time += timedelta(days=1)
                
                wait_seconds = (target_time - now).total_seconds()
                logger.info(f"⏰ Next financial data sync scheduled at {target_time} UTC ({wait_seconds/3600:.1f} hours from now)")
                await asyncio.sleep(wait_seconds)
            
            # Run the sync
            logger.info("🚀 Starting daily financial data sync for Nifty 50 stocks...")
            from services.nifty50_financial_sync import nifty50_financial_sync
            
            session = SessionLocal()
            try:
                result = await nifty50_financial_sync.sync_all_nifty50(session, max_concurrent=5)
                logger.info(f"✅ Daily sync completed: {result.get('message', 'Done')}")
            except Exception as e:
                logger.error(f"❌ Error in daily financial sync: {e}")
                import traceback
                logger.error(traceback.format_exc())
            finally:
                session.close()
                
        except asyncio.CancelledError:
            logger.info("Daily financial sync task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in daily financial sync loop: {e}")
            # If error occurs, wait 1 hour before retrying
            await asyncio.sleep(3600)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(sessions.router, prefix="/api/auth", tags=["Session Management"])
# Removed separate OTP routers; OTP flow is consolidated under Authentication routes
app.include_router(realtime.router, prefix="/api/realtime", tags=["Real-time Data"])
# Also register without /api prefix for frontend compatibility
app.include_router(realtime.router, prefix="/realtime", tags=["Real-time Data"])
app.include_router(trading.router, prefix="/api/trading", tags=["Trading"])
app.include_router(unified_ai.router, prefix="/api/unified-ai", tags=["Unified AI Analysis"])
# Also register without /api prefix for frontend compatibility
app.include_router(unified_ai.router, prefix="/unified-ai", tags=["Unified AI Analysis"])
app.include_router(risk.router, prefix="/api/risk", tags=["Risk Management"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Real-time Monitoring"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Chatbot"])
# Register education routes
app.include_router(education.router, prefix="/education", tags=["Education"])
app.include_router(education.router, prefix="/api/education", tags=["Education"])
app.include_router(intelligent_trading.router, prefix="/api/intelligent-trading", tags=["Intelligent Trading"])
# app.include_router(arpit_education.router, prefix="/api/arpit-education", tags=["Arpit Education"])  # Commented out - keeping for future use
# Portfolio Allocation routes (unified with holdings)
app.include_router(portfolio_allocation.router, prefix="/api/portfolio-allocation", tags=["Portfolio Allocation"])
app.include_router(charting.router, prefix="/api/charting", tags=["Advanced Charting"])
app.include_router(enhanced_charting.router, prefix="/api/enhanced-charting", tags=["Enhanced Charting"])
app.include_router(comprehensive_trading.router, prefix="/api/comprehensive-trading", tags=["Comprehensive Trading"])
app.include_router(consolidated_analysis.router, prefix="/api", tags=["Consolidated Analysis"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["NSE & BSE Stocks"])
app.include_router(model_training.router, tags=["Model Training"])  # Model training & performance monitoring
app.include_router(market_routes.router, prefix="/api/market", tags=["Market"])
# Public Nifty 50 routes (no authentication required)
from api.routes.nifty50_public import router as nifty50_public_router
app.include_router(nifty50_public_router, prefix="/api/public", tags=["Public Nifty 50"])
# Auto Trading Status routes
from api.routes.auto_trading_status import router as auto_trading_router
app.include_router(auto_trading_router, tags=["Auto Trading Status"])
app.include_router(market_dashboard.router, prefix="/api/market", tags=["Market Dashboard"])
# app.include_router(upstox_auth.router, prefix="/api/upstox", tags=["Upstox Integration"])  # REMOVED
app.include_router(candle_data.router, prefix="/api", tags=["Candlestick Data"])
app.include_router(trendlines.router, prefix="/api/trendlines", tags=["Trendline Detection"])
app.include_router(swing_points.router, prefix="/api/swing-points", tags=["Swing Point Analysis"])
app.include_router(market_structure.router, prefix="/api/market-structure", tags=["Market Structure (BOS/CHoCH)"])
app.include_router(support_resistance.router, prefix="/api/support-resistance", tags=["Support & Resistance"])
app.include_router(supply_demand.router, prefix="/api/supply-demand", tags=["Supply & Demand Zones"])
app.include_router(multi_timeframe.router, prefix="/api/multi-timeframe", tags=["Multi-Timeframe Analysis"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts System"])
app.include_router(backtesting.router, prefix="/api/backtesting", tags=["Backtesting Engine"])
app.include_router(screener.router, prefix="/api/screener", tags=["Stock Screener"])
app.include_router(financial_data.router, prefix="/api/financial", tags=["Financial Data"])
app.include_router(market_education.router, prefix="/api/market-education", tags=["Market Education"])
app.include_router(sync_jobs.router, prefix="/api/sync", tags=["Sync Jobs"])
app.include_router(market_factors.router, prefix="/api/market-factors", tags=["Market Factors"])
app.include_router(paper_trading.router, prefix="/api/paper-trading", tags=["Paper Trading"])
app.include_router(ml_training.router, prefix="/api", tags=["ML Training"])
app.include_router(social_trading_routes.router, tags=["Social Trading"])
app.include_router(advanced_orders_routes.router, tags=["Advanced Orders"])
app.include_router(analytics_routes.router, tags=["Analytics"])
app.include_router(user_learning.router, prefix="/api/user-learning", tags=["User Learning & Feedback"])
app.include_router(advanced_learning.router, prefix="/api/advanced-learning", tags=["Advanced Learning"])
app.include_router(trading_performance_router, tags=["Trading Performance"])  # Trading Performance endpoints
app.include_router(nifty50_performance_router, tags=["Nifty50 Performance"])  # Nifty50 Performance endpoints
app.include_router(simple_portfolio_router, prefix="/api/simple-portfolio", tags=["Simple Portfolio"])
app.include_router(order_book_router, prefix="/api/order-book", tags=["Order Book"])
app.include_router(holdings_router, prefix="/api/holdings", tags=["Holdings"])
app.include_router(realtime_trading_router, tags=["Real-time Trading"])  # Real-time Trading endpoints

# Technical Indicators API
from api.technical_indicators_api import router as technical_indicators_router
app.include_router(technical_indicators_router, prefix="/api", tags=["Technical Indicators"])

# Also register routes without /api prefix for frontend compatibility
app.include_router(risk.router, prefix="/risk", tags=["Risk Management"])
app.include_router(trading.router, prefix="/trading", tags=["Trading"])
app.include_router(portfolio_allocation.router, prefix="/portfolio-allocation", tags=["Portfolio Allocation"])
app.include_router(intelligent_trading.router, prefix="/intelligent-trading", tags=["Intelligent Trading"])
app.include_router(comprehensive_trading.router, prefix="/comprehensive-trading", tags=["Comprehensive Trading"])
app.include_router(financial_data.router, prefix="/financial", tags=["Financial Data"])

# Test endpoint
@app.get("/api/v1/test-endpoint")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Backend is working", "status": "success"}

# Trading orders endpoint - matches the working frontend code
@app.get("/api/trading/orders")
async def get_trading_orders(current_user: User = Depends(get_current_active_user)):
    """Get trading orders for the current user"""
    try:
        # Use direct database connection
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine, text
        
        database_url = "sqlite:///D:/Trader_AI_WEB_V_0.3/Trader_AI_V_0.1/trader_ai.db"
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Get all orders for the user
            orders = session.execute(text("""
                SELECT id, symbol, status, entry_price, quantity, notes, created_at, entry_time, exit_time, exit_price
                FROM trading_executions 
                WHERE user_id = :user_id
                ORDER BY id DESC
            """), {'user_id': current_user.id}).fetchall()
            
            # Format response to match frontend expectations
            formatted_orders = []
            for order in orders:
                formatted_orders.append({
                    'id': order[0],
                    'symbol': order[1],
                    'order_status': order[2],
                    'order_type': 'BUY',  # Default to BUY
                    'order_side': 'LIMIT',  # Default to LIMIT
                    'price': order[3],
                    'quantity': order[4],
                    'notes': order[5],
                    'created_at': order[6] or order[7],
                    'execution_time': order[8],
                    'filled_price': order[9] or order[3]
                })
            
            return {
                'success': True,
                'orders': formatted_orders
            }
            
        finally:
            session.close()
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Trading cancel order endpoint
@app.delete("/api/trading/cancel-order/{order_id}")
async def cancel_trading_order(order_id: int, current_user: User = Depends(get_current_active_user)):
    """Cancel a trading order"""
    try:
        # Use direct database connection
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine, text
        from datetime import datetime
        
        database_url = "sqlite:///D:/Trader_AI_WEB_V_0.3/Trader_AI_V_0.1/trader_ai.db"
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # First check if the order exists and belongs to the user
            order_check = session.execute(text("""
                SELECT id, symbol, status, user_id 
                FROM trading_executions 
                WHERE id = :order_id AND user_id = :user_id
            """), {'order_id': order_id, 'user_id': current_user.id}).fetchone()
            
            if not order_check:
                return {
                    'success': False,
                    'error': f'Order {order_id} not found or does not belong to user'
                }
            
            order_id_db, symbol, status, user_id = order_check
            
            # Check if order can be cancelled
            if status not in ['PENDING', 'OPEN']:
                return {
                    'success': False,
                    'error': f'Cannot cancel order {order_id} with status {status}. Only PENDING or OPEN orders can be cancelled.'
                }
            
            # Cancel the order
            session.execute(text("""
                UPDATE trading_executions 
                SET status = 'CANCELLED', 
                    exit_time = :exit_time,
                    notes = CASE 
                        WHEN notes IS NULL OR notes = '' THEN 'Cancelled by user at ' || :exit_time
                        ELSE notes || '\nCancelled by user at ' || :exit_time
                    END
                WHERE id = :order_id AND user_id = :user_id
            """), {
                'order_id': order_id, 
                'user_id': current_user.id,
                'exit_time': datetime.utcnow().isoformat()
            })
            
            session.commit()
            
            return {
                'success': True,
                'message': f'Order {order_id} ({symbol}) cancelled successfully'
            }
            
        except Exception as db_error:
            session.rollback()
            return {
                'success': False,
                'error': f'Database error: {str(db_error)}'
            }
        finally:
            session.close()
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Server error: {str(e)}'
        }

# Direct Portfolio Endpoint - Quick fix for frontend visibility
@app.get("/api/v1/direct-portfolio")
async def get_direct_portfolio(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Direct portfolio access for tester2 - immediate frontend visibility"""
    try:
        # Get portfolio holdings
        holdings = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
        
        # Get recent trades
        from datetime import datetime, timedelta
        executions = db.query(TradingExecution).filter(
            TradingExecution.created_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        # Format holdings
        formatted_holdings = {}
        total_value = 0
        for holding in holdings:
            holding_value = holding.quantity * holding.current_price
            total_value += holding_value
            formatted_holdings[holding.symbol] = {
                'quantity': holding.quantity,
                'avg_price': holding.average_price,
                'current_price': holding.current_price,
                'total_value': holding_value,
                'unrealized_pnl': (holding.current_price - holding.average_price) * holding.quantity,
                'unrealized_pnl_percent': ((holding.current_price - holding.average_price) / holding.average_price * 100) if holding.average_price > 0 else 0
            }
        
        # Format trades
        formatted_trades = []
        for exec in executions:
            formatted_trades.append({
                'symbol': exec.symbol,
                'signal_type': exec.signal_type,
                'quantity': exec.quantity,
                'entry_price': exec.entry_price,
                'entry_value': exec.entry_value,
                'status': exec.status,
                'created_at': exec.created_at.isoformat() if exec.created_at else None
            })
        
        return {
            'success': True,
            'data': {
                'holdings': formatted_holdings,
                'total_value': total_value,
                'holding_count': len(holdings),
                'trades': formatted_trades,
                'trade_count': len(executions)
            },
            'message': f'Portfolio data for {current_user.username}'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio: {str(e)}")

# Debug endpoint removed for security - was exposing user object structure

# Order Book Endpoint - Direct fix for frontend visibility
@app.get("/api/v1/order-book/executed-orders")
async def get_executed_orders_direct(
    current_user: User = Depends(get_current_active_user),
    days: int = 30
):
    """Get all executed orders for the current user"""
    try:
        # Get user ID from the dict or object
        if isinstance(current_user, dict):
            user_id = current_user.get('id')
        else:
            user_id = current_user.id
        
        print(f"🔍 Fetching orders for user_id: {user_id}")
        
        # Use direct database connection to ensure correct database
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        
        database_url = "sqlite:///./trader_ai.db"
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        print(f"🔍 ORDER BOOK: Using database: {database_url}")
        
        # Get recent executions for specific user
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        executions = db.query(TradingExecution).filter(
            TradingExecution.user_id == user_id,
            TradingExecution.created_at >= cutoff_date
        ).order_by(TradingExecution.created_at.desc()).all()
        
        print(f"📊 Found {len(executions)} executions for user {user_id}")
        
        # Format executions for order book
        formatted_orders = []
        for exec in executions:
            # Calculate P&L if trade is closed
            pnl_amount = exec.pnl_amount
            pnl_percent = exec.pnl_percent
            
            # Determine order status - preserve CANCELLED status explicitly
            status = exec.status
            if status == "OPEN":
                status_display = "PENDING"  # OPEN orders are pending
            elif status == "CLOSED":
                status_display = "EXECUTED"  # CLOSED orders are executed
            elif status == "CANCELLED":
                status_display = "CANCELLED"  # Preserve cancelled status
            elif status == "ACTIVE":
                status_display = "EXECUTED"  # ACTIVE means executed
            else:
                status_display = status  # Keep other statuses as-is
            
            order_data = {
                'id': exec.id,
                'symbol': exec.symbol,
                'signal_type': exec.signal_type,
                'action': exec.action,
                'quantity': exec.quantity,
                'entry_price': exec.entry_price,
                'entry_value': exec.entry_value,
                'exit_price': exec.exit_price,
                'exit_value': exec.exit_value,
                'pnl_amount': pnl_amount,
                'pnl_percent': pnl_percent,
                'status': status_display,
                'entry_time': exec.entry_time.isoformat() if exec.entry_time else None,
                'exit_time': exec.exit_time.isoformat() if exec.exit_time else None,
                'holding_period_hours': exec.holding_period_hours,
                'created_at': exec.created_at.isoformat() if exec.created_at else None,
                'updated_at': exec.updated_at.isoformat() if exec.updated_at else None,
                'notes': exec.notes
            }
            
            # Add additional info from notes
            if exec.notes:
                try:
                    # Parse strategy info from notes
                    notes_str = exec.notes
                    if 'Strategy:' in notes_str:
                        parts = notes_str.split(',')
                        for part in parts:
                            if 'Strategy:' in part:
                                order_data['strategy'] = part.split(':')[1].strip()
                            elif 'Confidence:' in part:
                                order_data['confidence'] = float(part.split(':')[1].strip())
                            elif 'Signal Strength:' in part:
                                order_data['signal_strength'] = part.split(':')[1].strip()
                            elif 'Target:' in part:
                                order_data['target_price'] = float(part.split(':')[1].strip())
                            elif 'Stop Loss:' in part:
                                order_data['stop_loss'] = float(part.split(':')[1].strip())
                except:
                    pass
            
            formatted_orders.append(order_data)
        
        # Calculate summary statistics
        total_orders = len(formatted_orders)
        pending_orders = len([o for o in formatted_orders if o['status'] == 'PENDING'])
        executed_orders = len([o for o in formatted_orders if o['status'] == 'EXECUTED'])
        cancelled_orders = len([o for o in formatted_orders if o['status'] == 'CANCELLED'])
        
        # Calculate total P&L for executed orders
        total_pnl = sum([o['pnl_amount'] or 0 for o in formatted_orders if o['pnl_amount'] is not None and o['status'] == 'EXECUTED'])
        
        return {
            'success': True,
            'data': {
                'orders': formatted_orders,
                'summary': {
                    'total_orders': total_orders,
                    'pending_orders': pending_orders,
                    'executed_orders': executed_orders,
                    'cancelled_orders': cancelled_orders,
                    'total_pnl': total_pnl,
                    'period_days': days
                }
            },
            'message': f'Order book for user - Last {days} days'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order book: {str(e)}")

# Duplicate order book endpoint removed - using /api/v1/order-book/executed-orders instead
# Also register without /api/v1 prefix for backward compatibility
app.get("/api/order-book/executed-orders")(get_executed_orders_direct)

# Limit order monitoring function - DISABLED FOR NOW
# async def _start_limit_order_monitoring():
#     """Start monitoring pending limit orders"""
#     pass

# async def _check_market_close_and_cancel_orders(session):
#     """Check if market is closed and cancel pending limit orders"""
#     pass

# cancel_limit_order function removed - using direct SQL in endpoint

async def _check_single_order(order, session):
    """Check if a single limit order should be executed"""
    try:
        # Handle both dict and model object
        if isinstance(order, dict):
            symbol = order.get('symbol')
            notes = order.get('notes', '')
            signal_type = order.get('signal_type')
            entry_price = order.get('entry_price')
            quantity = order.get('quantity')
            entry_value = order.get('entry_value')
        else:
            symbol = order.symbol
            notes = order.notes
            signal_type = order.signal_type
            entry_price = order.entry_price
            quantity = order.quantity
            entry_value = order.entry_value
        
        # Get current market price
        current_price_data = await data_service.get_current_price(symbol)
        
        if not current_price_data or 'current_price' not in current_price_data:
            logger.warning(f"Could not get current price for {symbol}")
            return
        
        current_price = current_price_data['current_price']
        
        # Extract target price from notes
        target_price = None
        if notes and 'Target:' in notes:
            try:
                target_price = float(notes.split('Target:')[1].split(',')[0].strip())
            except:
                target_price = None
        
        logger.info(f"🔍 Checking {symbol}: Target={target_price}, Current={current_price}, Action={signal_type}")
        
        # Check if price matches for execution
        should_execute = False
        
        if signal_type == 'BUY':
            # Buy order: execute when current price <= target price
            should_execute = current_price <= target_price
        else:  # SELL
            # Sell order: execute when current price >= target price
            should_execute = current_price >= target_price
        
        if should_execute:
            logger.info(f"✅ Executing limit order: {symbol} at {current_price}")
            
            # Update order to executed status
            if isinstance(order, dict):
                order_id = order.get('id')
            else:
                order_id = order.id
            
            # Update the order in database
            session.query(TradingExecution).filter(TradingExecution.id == order_id).update({
                'status': 'EXECUTED',
                'exit_price': current_price,
                'exit_value': current_price * quantity,
                'exit_time': datetime.utcnow(),
                'pnl_amount': (current_price - entry_price) * quantity if signal_type == 'BUY' else (entry_price - current_price) * quantity,
                'pnl_percent': ((current_price - entry_price) / entry_price * 100 if signal_type == 'BUY' else (entry_price - current_price) / entry_price * 100) if entry_value != 0 else 0,
                'profit_loss': 'PROFIT' if (current_price - entry_price) * quantity > 0 else 'LOSS' if (current_price - entry_price) * quantity < 0 else 'BREAKEVEN'
            })
            
            logger.info(f"💰 Order executed: {symbol}")
            
        else:
            # Order still pending
            logger.debug(f"⏳ Order still pending: {symbol}")
            
    except Exception as e:
        logger.error(f"Error checking order: {e}")

# Cancel limit order endpoint
@app.post("/api/order-book/cancel-order/{order_id}")
async def cancel_order_endpoint(
    order_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel a pending order"""
    try:
        # Get user ID from the dict or object
        if isinstance(current_user, dict):
            user_id = current_user.get('id')
        else:
            user_id = current_user.id
        
        print(f"🔍 Starting cancel order for ID: {order_id}")
        print(f"🔍 Current user type: {type(current_user)}")
        
        # Use direct database connection to ensure correct database
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        
        database_url = "sqlite:///D:/Trader_AI_WEB_V_0.3/Trader_AI_V_0.1/trader_ai.db"
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        try:
            # Find the order with user filtering
            order = db.query(TradingExecution).filter(
                TradingExecution.id == order_id,
                TradingExecution.user_id == user_id
            ).first()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Check if order can be cancelled (only PENDING or OPEN orders)
            if order.status not in ['PENDING', 'OPEN']:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot cancel order with status: {order.status}. Only PENDING or OPEN orders can be cancelled."
                )
        
        # Update order status to CANCELLED
            order.status = 'CANCELLED'
            order.exit_time = datetime.utcnow()
            
            # Update notes with cancellation info
            cancellation_note = f'Manually cancelled by user {user_id} at {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}'
            if order.notes:
                order.notes = f"{order.notes}\n{cancellation_note}"
            else:
                order.notes = cancellation_note
            
            db.commit()
            db.refresh(order)
            
            logger.info(f"✅ Order {order_id} (symbol: {order.symbol}) cancelled successfully")
            
            return {
                'success': True,
                'data': {
                    'order_id': order_id,
                    'symbol': order.symbol,
                    'status': 'CANCELLED'
                },
                'message': f'Order {order_id} cancelled successfully'
            }
        finally:
            db.close()
            
    except HTTPException:
        if 'db' in locals():
            db.close()
        raise
    except Exception as e:
        if 'db' in locals():
            db.rollback()
            db.close()
        logger.error(f"Error cancelling order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error cancelling order: {str(e)}")

# Test endpoint without authentication
@app.post("/api/test-cancel-order/{order_id}")
async def test_cancel_order_endpoint(order_id: int):
    """Test cancel order without authentication"""
    try:
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine, text
        from datetime import datetime
        
        database_url = "sqlite:///./trader_ai.db"
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Update the order directly
            result = session.execute(text("""
                UPDATE trading_executions 
                SET status = 'CANCELLED',
                    notes = 'Test cancellation',
                    exit_time = :exit_time
                WHERE id = :order_id AND status = 'PENDING'
            """), {
                'order_id': order_id,
                'exit_time': datetime.utcnow()
            })
            
            session.commit()
            
            if result.rowcount > 0:
                logger.info(f"❌ Test cancelled limit order (ID: {order_id})")
                return {
                    'success': True,
                    'message': f'Order {order_id} cancelled successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Order not found or cannot be cancelled'
                }
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error cancelling order {order_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error cancelling order: {str(e)}")
        finally:
            session.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling order: {str(e)}")

# WebSocket endpoint with enhanced user management
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Extract user ID from query parameters or headers
    user_id = "anonymous"  # Default for anonymous users
    
    try:
        # Try to get user ID from query parameters
        query_params = websocket.query_params
        if "user_id" in query_params:
            user_id = query_params["user_id"]
        
        await websocket_manager.connect(websocket, user_id)
        
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await websocket_manager.handle_message(websocket, user_id, message)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from user {user_id}: {data}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        websocket_manager.disconnect(user_id)

# Nifty50 WebSocket endpoint for real-time updates
@app.websocket("/ws/nifty50")
async def nifty50_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Nifty50 real-time trading signals"""
    from api.websocket_handler import websocket_endpoint as nifty50_handler
    
    # Use the dedicated Nifty50 WebSocket handler
    await nifty50_handler(websocket, "nifty50_updates")

# Health check endpoints for AWS load balancer
@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Comprehensive health check for AWS load balancer"""
    try:
        # Check database connection
        from core.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    try:
        # Check Redis connection
        from core.redis_client import redis_client
        await redis_client.connect()
        redis_status = "healthy" if await redis_client.ping() else "unhealthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy"
    
    return {
        "status": overall_status,
        "message": "Trader AI is running",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "redis": redis_status
        }
    }

# Serve React build
FRONTEND_BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend_build_resolved"))

# Resolve actual frontend build directory (../frontend/build)
_candidate_build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "build"))
if os.path.exists(_candidate_build_dir):
    FRONTEND_BUILD_DIR = _candidate_build_dir

# Mount static assets under /static (from React build)
static_dir = os.path.join(FRONTEND_BUILD_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Root serves React index.html
@app.get("/")
async def serve_root():
    index_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {
        "message": "Welcome to Trader AI - Indian Stock Market Platform",
        "version": "1.0.0",
        "docs": "/docs"
    }

# API Status endpoint - MUST be before catch-all route
@app.get("/api/status")
async def get_api_status():
    """Get API status and health information"""
    try:
        status = {
            "api_status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": "healthy",
                "redis": "unhealthy",
                "trading_apis": "healthy"
            }
        }
        return {"success": True, "data": status}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Catch-all to support client-side routing, excluding API and WS paths
@app.get("/{full_path:path}")
async def serve_spa(full_path: str, request: Request):
    # Skip OPTIONS requests (handled by CORS middleware and OPTIONS handlers)
    if request.method == "OPTIONS":
        from fastapi.responses import Response
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "3600",
            }
        )
    
    if full_path.startswith("api/") or full_path.startswith("ws") or full_path == "docs" or full_path.startswith("redoc"):
        # Let API/docs/ws be handled by their own routes
        raise HTTPException(status_code=404, detail="Not Found")
    index_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Frontend build not found")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )
