"""
Portfolio Allocation API Routes
AI-powered portfolio optimization and allocation strategies
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from core.database import get_db
from core.auth_dependencies import get_current_user, get_current_active_user
from services.portfolio_allocation_service import portfolio_allocation_service
from services.portfolio_optimization import portfolio_optimization_service
from core.database_unified import User, PortfolioMetadata
from services.data_fetcher import fetch_historical_data
import pandas as pd
import numpy as np

# Helper function to avoid SQLite LIMIT/OFFSET parameter issues
def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID avoiding SQLite LIMIT/OFFSET parameter binding issues"""
    try:
        users = db.query(User).filter(User.id == user_id).all()
        return users[0] if users else None
    except Exception as e:
        logger.error(f"Error querying user {user_id}: {e}")
        return None

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/optimize")
async def optimize_portfolio(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Optimize portfolio allocation using AI"""
    try:
        user_preferences = request_data.get("preferences", {})
        risk_tolerance = request_data.get("risk_tolerance", "medium")
        investment_amount = request_data.get("amount", 100000)
        
        result = await portfolio_allocation_service.optimize_allocation(
            user_preferences=user_preferences,
            risk_tolerance=risk_tolerance,
            investment_amount=investment_amount
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Portfolio optimization completed successfully"
        }
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies")
async def get_allocation_strategies(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get available portfolio allocation strategies"""
    try:
        result = await portfolio_allocation_service.get_allocation_strategies()
        return {
            "success": True,
            "data": result,
            "message": "Allocation strategies retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting allocation strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebalance")
async def rebalance_portfolio(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Rebalance existing portfolio"""
    try:
        # Handle both User object and dict
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        
        # Get current portfolio from holdings if not provided
        if "portfolio" not in request_data:
            holdings_result = await portfolio_allocation_service.get_holdings(user_id, db)
            holdings = holdings_result.get("holdings", [])
            total_value = holdings_result.get("total_value", 0.0)
            current_allocation = portfolio_allocation_service.calculate_allocation_from_holdings(holdings, total_value)
            request_data["portfolio"] = {
                "allocation": current_allocation,
                "holdings": holdings,
                "total_value": total_value
            }
        
        current_portfolio = request_data.get("portfolio", {})
        rebalance_frequency = request_data.get("frequency", "quarterly")
        
        result = await portfolio_allocation_service.rebalance_portfolio(
            current_portfolio=current_portfolio,
            frequency=rebalance_frequency
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Portfolio rebalancing completed successfully"
        }
    except Exception as e:
        logger.error(f"Error rebalancing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-portfolio")
async def optimize_portfolio_mpt(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Optimize portfolio using Modern Portfolio Theory"""
    try:
        symbols = request_data.get("symbols", [])
        optimization_type = request_data.get("optimization_type", "max_sharpe")
        constraints = request_data.get("constraints", {})
        days = request_data.get("days", 252)  # 1 year of data
        
        if not symbols or len(symbols) < 2:
            raise HTTPException(status_code=400, detail="At least 2 symbols required for optimization")
        
        # Fetch historical data for all symbols
        price_data = {}
        for symbol in symbols:
            try:
                candles = await fetch_historical_data(symbol, "1d", days=days)
                if candles and len(candles) > 0:
                    df = pd.DataFrame(candles)
                    df['date'] = pd.to_datetime(df['time'], unit='s')
                    df.set_index('date', inplace=True)
                    price_data[symbol] = df['close']
            except Exception as e:
                logger.warning(f"Could not fetch data for {symbol}: {e}")
                continue
        
        if len(price_data) < 2:
            raise HTTPException(status_code=400, detail="Insufficient data for optimization")
        
        # Align all price series
        prices_df = pd.DataFrame(price_data)
        prices_df = prices_df.dropna()
        
        if len(prices_df) < 30:
            raise HTTPException(status_code=400, detail="Insufficient historical data (need at least 30 days)")
        
        # Calculate returns and covariance
        returns_df = prices_df.pct_change().dropna()
        expected_returns = portfolio_optimization_service.calculate_expected_returns(returns_df)
        covariance_matrix = portfolio_optimization_service.calculate_covariance_matrix(returns_df)
        
        # Optimize portfolio
        result = portfolio_optimization_service.optimize_portfolio(
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            optimization_type=optimization_type,
            constraints=constraints
        )
        
        # Generate efficient frontier
        efficient_frontier = portfolio_optimization_service.generate_efficient_frontier(
            expected_returns,
            covariance_matrix,
            num_points=20
        )
        
        return {
            "success": True,
            "optimization": result,
            "efficient_frontier": efficient_frontier,
            "symbols": symbols,
            "data_points": len(prices_df)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebalance-portfolio")
async def rebalance_portfolio_mpt(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Calculate rebalancing actions for current portfolio"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        
        # Get current holdings
        holdings_result = await portfolio_allocation_service.get_holdings(user_id, db)
        holdings = holdings_result.get("holdings", [])
        total_value = holdings_result.get("total_value", 0.0)
        
        if not holdings or total_value == 0:
            raise HTTPException(status_code=400, detail="No holdings found")
        
        # Get target allocation from optimization
        symbols = [h["symbol"] for h in holdings]
        optimization_type = request_data.get("optimization_type", "max_sharpe")
        
        # Fetch data and optimize
        price_data = {}
        for symbol in symbols:
            try:
                candles = await fetch_historical_data(symbol, "1d", days=252)
                if candles and len(candles) > 0:
                    df = pd.DataFrame(candles)
                    df['date'] = pd.to_datetime(df['time'], unit='s')
                    df.set_index('date', inplace=True)
                    price_data[symbol] = df['close']
            except Exception as e:
                logger.warning(f"Could not fetch data for {symbol}: {e}")
                continue
        
        if len(price_data) < 2:
            raise HTTPException(status_code=400, detail="Insufficient data for rebalancing")
        
        prices_df = pd.DataFrame(price_data).dropna()
        returns_df = prices_df.pct_change().dropna()
        expected_returns = portfolio_optimization_service.calculate_expected_returns(returns_df)
        covariance_matrix = portfolio_optimization_service.calculate_covariance_matrix(returns_df)
        
        # Optimize
        optimization_result = portfolio_optimization_service.optimize_portfolio(
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            optimization_type=optimization_type
        )
        
        # Calculate current weights
        current_weights = {}
        for holding in holdings:
            symbol = holding["symbol"]
            value = holding.get("total_value", 0)
            if total_value > 0:
                current_weights[symbol] = value / total_value
        
        # Calculate target weights
        target_weights = {}
        for i, symbol in enumerate(optimization_result["symbols"]):
            if symbol in symbols:
                target_weights[symbol] = optimization_result["weights"][i]
        
        # Calculate rebalancing actions
        actions = portfolio_optimization_service.calculate_rebalancing_actions(
            current_weights=current_weights,
            target_weights=target_weights,
            total_value=total_value
        )
        
        return {
            "success": True,
            "current_allocation": current_weights,
            "target_allocation": target_weights,
            "rebalancing_actions": actions,
            "optimization_metrics": optimization_result["metrics"],
            "total_value": total_value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rebalancing portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Missing Endpoints for API Compatibility ----------

@router.get("/holdings")
async def get_holdings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's stock holdings with live price updates and PnL calculations"""
    try:
        # Handle both User object and dict
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        
        result = await portfolio_allocation_service.get_holdings(user_id, db)
        return {
            "success": True,
            "data": result,
            "message": "Holdings retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-portfolio")
async def create_portfolio(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new portfolio with metadata"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        
        # Get portfolio data from request
        name = request_data.get("name", "My Portfolio")
        description = request_data.get("description", "")
        total_value = request_data.get("total_value", 0.0)
        
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Portfolio name is required")
        
        # Initialize wallet balance first
        if total_value > 0:
            try:
                db_user = get_user_by_id(db, user_id)
                if db_user:
                    db_user.demo_cash_balance = float(total_value)
                    db.commit()
                    logger.info(f"Set wallet balance for user {user_id} to ₹{total_value:,.2f}")
            except Exception as wallet_error:
                logger.warning(f"Failed to initialize wallet balance: {wallet_error}")
        
        # Create portfolio metadata
        portfolio_metadata = PortfolioMetadata(
            user_id=user_id,
            name=name.strip(),
            description=description.strip() if description else None,
            total_value=float(total_value) if total_value > 0 else 0.0,
            is_active=True
        )
        
        db.add(portfolio_metadata)
        db.commit()
        db.refresh(portfolio_metadata)
        
        logger.info(f"Created portfolio '{name}' for user {user_id} with total_value ₹{total_value:,.2f}")
        
        return {
            "success": True,
            "data": {
                "id": portfolio_metadata.id,
                "name": portfolio_metadata.name,
                "description": portfolio_metadata.description,
                "total_value": portfolio_metadata.total_value,
                "is_active": portfolio_metadata.is_active,
                "created_at": portfolio_metadata.created_at.isoformat() if portfolio_metadata.created_at else None,
                "updated_at": portfolio_metadata.updated_at.isoformat() if portfolio_metadata.updated_at else None
            },
            "message": "Portfolio created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolios")
async def get_user_portfolios(
    # current_user: User = Depends(get_current_active_user),  # Temporarily disabled for testing
    db: Session = Depends(get_db)
):
    """Get all portfolios for the current user"""
    try:
        # Use hardcoded user_id for testing
        user_id = 1
        
        portfolios = db.query(PortfolioMetadata).filter(
            PortfolioMetadata.user_id == user_id,
            PortfolioMetadata.is_active == True
        ).order_by(PortfolioMetadata.created_at.desc()).all()
        
        portfolio_list = []
        for p in portfolios:
            # Get holdings for this portfolio
            from core.database_unified import Portfolio
            holdings = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            
            # Calculate portfolio value from holdings
            holdings_result = await portfolio_allocation_service.get_holdings(user_id, db)
            total_value = holdings_result.get("total_value", 0.0)
            total_invested = holdings_result.get("total_invested", 0.0)
            total_pnl = holdings_result.get("total_pnl", 0.0)
            
            portfolio_list.append({
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "total_value": total_value,
                "total_invested": total_invested,
                "total_pnl": total_pnl,
                "initial_allocation": p.total_value,
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            })
        
        return {
            "success": True,
            "data": portfolio_list,
            "message": "Portfolios retrieved successfully"
        }
    except Exception as e:
        import sqlalchemy.exc as sa_exc
        error_msg = str(e)
        
        # Handle SQLite connection errors gracefully
        if isinstance(e, (sa_exc.ProgrammingError, sa_exc.OperationalError)) and "closed database" in error_msg.lower():
            logger.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail="Database connection error. Please try again.")
        else:
            logger.error(f"Error getting portfolios: {e}")
            raise HTTPException(status_code=500, detail=error_msg)

@router.get("/portfolio")
async def get_unified_portfolio(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get unified portfolio with both holdings and allocation"""
    try:
        # Handle both User object and dict
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        
        # Get user's wallet balance - use helper to avoid SQLite LIMIT/OFFSET parameter issues
        db_user = get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get holdings first to check if user has existing portfolio
        holdings_result = await portfolio_allocation_service.get_holdings(user_id, db)
        holdings = holdings_result.get("holdings", [])
        total_value = holdings_result.get("total_value", 0.0)
        total_pnl = holdings_result.get("total_pnl", 0.0)
        
        # Get wallet balance - prioritize demo_cash_balance
        wallet_balance = 0.0
        if db_user.demo_cash_balance is not None:
            wallet_balance = float(db_user.demo_cash_balance)
        elif db_user.real_cash_balance is not None:
            wallet_balance = float(db_user.real_cash_balance)
        
        logger.info(f"User {user_id} wallet balance: demo={db_user.demo_cash_balance}, real={db_user.real_cash_balance}, calculated={wallet_balance}")
        
        # If wallet balance is 0 and user has holdings, initialize with default demo balance
        # This handles the case where user has existing holdings but wallet was never initialized
        if wallet_balance == 0.0 and total_value > 0:
            if db_user.demo_cash_balance is None or db_user.demo_cash_balance == 0.0:
                db_user.demo_cash_balance = 1000000.0  # Default demo balance
                wallet_balance = 1000000.0
                db.commit()
                db.refresh(db_user)
                logger.info(f"Auto-initialized wallet balance for user {user_id} with existing holdings: ₹{wallet_balance:,.2f}")
        
        # Calculate total allocated cash = wallet balance + total invested
        # This represents the initial cash allocation set during portfolio creation
        total_invested = holdings_result.get("total_invested", 0.0)
        total_allocated_cash = wallet_balance + total_invested
        
        # Calculate total net worth = wallet balance + portfolio value
        total_net_worth = wallet_balance + total_value
        
        # Calculate allocation from holdings
        current_allocation = portfolio_allocation_service.calculate_allocation_from_holdings(holdings, total_value)
        
        # Get target allocation (can be stored in user preferences or use default)
        target_allocation = {
            "equity": 60.0,
            "bonds": 25.0,
            "cash": 10.0,
            "commodities": 5.0
        }
        
        # Analyze allocation drift
        allocation_analysis = portfolio_allocation_service._analyze_allocation(
            {"allocation": current_allocation},
            target_allocation
        )
        
        return {
            "success": True,
            "data": {
                "holdings": holdings,
                "holdings_summary": {
                    "total_value": total_value,
                    "total_invested": holdings_result.get("total_invested", 0.0),
                    "total_pnl": total_pnl,
                    "total_pnl_percent": holdings_result.get("total_pnl_percent", 0.0),
                    "wallet_balance": wallet_balance,
                    "total_allocated_cash": total_allocated_cash,
                    "total_net_worth": total_net_worth,
                    "currency": "INR",
                    "currency_symbol": "₹",
                    "formatted_wallet_balance": f"₹{wallet_balance:,.2f}",
                    "formatted_total_allocated_cash": f"₹{total_allocated_cash:,.2f}",
                    "formatted_total_net_worth": f"₹{total_net_worth:,.2f}"
                },
                "allocation": {
                    "current": current_allocation,
                    "target": target_allocation,
                    "drift": allocation_analysis,
                    "rebalancing_needed": allocation_analysis.get("needs_rebalancing", False)
                },
                "last_updated": datetime.utcnow().isoformat()
            },
            "message": "Unified portfolio retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting unified portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/allocation")
async def get_allocation(
    # current_user: User = Depends(get_current_active_user),  # Temporarily disabled for testing
    db: Session = Depends(get_db)
):
    """Get portfolio allocation (calculated from holdings)"""
    try:
        # Use hardcoded user_id for testing (normally would get from current_user)
        user_id = 1
        
        # Get holdings to calculate allocation
        holdings_result = await portfolio_allocation_service.get_holdings(user_id, db)
        holdings = holdings_result.get("holdings", [])
        total_value = holdings_result.get("total_value", 0.0)
        
        # Calculate allocation from holdings
        current_allocation = portfolio_allocation_service.calculate_allocation_from_holdings(holdings, total_value)
        
        return {
            "success": True,
            "data": {
                "allocation": current_allocation,
                "target_allocation": {
                    "equity": 60.0,
                    "debt": 25.0,
                    "cash": 10.0,
                    "commodities": 5.0
                },
                "recommendations": ["Rebalance quarterly", "Monitor risk exposure"]
            },
            "message": "Portfolio allocation retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting allocation: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting allocation: {str(e)}")

@router.get("/ai-signals")
async def get_ai_signals(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI signals from research reports for portfolio holdings"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        result = await portfolio_allocation_service.get_ai_signals_from_reports(user_id, db)
        return {
            "success": result.get("success", True),
            "data": result,
            "message": "AI signals retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting AI signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-metrics")
async def get_risk_metrics(
    period_days: int = Query(252, description="Period in days for calculation"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get real risk metrics (Sharpe, Beta) from historical data"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        result = await portfolio_allocation_service.calculate_real_risk_metrics(user_id, db, period_days)
        return {
            "success": result.get("success", True),
            "data": result,
            "message": "Risk metrics calculated successfully"
        }
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sector-allocation")
async def get_sector_allocation(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get sector allocation for portfolio holdings"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        result = await portfolio_allocation_service.get_sector_allocation(user_id, db)
        return {
            "success": result.get("success", True),
            "data": result,
            "message": "Sector allocation retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting sector allocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/volume-analysis")
async def get_volume_analysis(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get real volume analysis for portfolio holdings"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        result = await portfolio_allocation_service.get_volume_analysis(user_id, db)
        return {
            "success": result.get("success", True),
            "data": result,
            "message": "Volume analysis retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting volume analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-insights")
async def get_market_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI insights from market intelligence"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        result = await portfolio_allocation_service.get_market_intelligence_insights(user_id, db)
        return {
            "success": result.get("success", True),
            "data": result,
            "message": "Market insights retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting market insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize-wallet")
async def initialize_wallet(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Initialize or update wallet balance when creating a portfolio"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        
        # Get user from database
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get initial balance from request (portfolio total_value)
        initial_balance = request_data.get("total_value", 0.0)
        is_demo = request_data.get("is_demo", True)  # Default to demo mode
        
        logger.info(f"Initializing wallet for user {user_id}: initial_balance=₹{initial_balance:,.2f}, is_demo={is_demo}")
        
        # Get current wallet balance
        if is_demo:
            current_balance = float(db_user.demo_cash_balance) if db_user.demo_cash_balance is not None else 0.0
            logger.info(f"User {user_id} current demo balance: ₹{current_balance:,.2f}, initial_balance requested: ₹{initial_balance:,.2f}")
            
            # Always SET the wallet balance to the portfolio value when creating a new portfolio
            # This ensures the wallet reflects the allocated cash for the portfolio
            if initial_balance > 0:
                db_user.demo_cash_balance = float(initial_balance)
                logger.info(f"Set demo wallet balance for user {user_id} to ₹{db_user.demo_cash_balance:,.2f}")
            elif current_balance == 0.0 or db_user.demo_cash_balance is None:
                # If no initial balance provided and current is 0, use default
                db_user.demo_cash_balance = 1000000.0
                logger.info(f"Initialized demo wallet balance for user {user_id} to default: ₹{db_user.demo_cash_balance:,.2f}")
        else:
            current_balance = float(db_user.real_cash_balance) if db_user.real_cash_balance is not None else 0.0
            logger.info(f"User {user_id} current real balance: ₹{current_balance:,.2f}, initial_balance requested: ₹{initial_balance:,.2f}")
            
            # Always SET the wallet balance to the portfolio value
            if initial_balance > 0:
                db_user.real_cash_balance = float(initial_balance)
                logger.info(f"Set real wallet balance for user {user_id} to ₹{db_user.real_cash_balance:,.2f}")
            elif current_balance == 0.0 or db_user.real_cash_balance is None:
                db_user.real_cash_balance = 0.0
                logger.info(f"Initialized real wallet balance for user {user_id} to ₹0.00")
        
        db.commit()
        db.refresh(db_user)
        
        final_balance = float(db_user.demo_cash_balance) if is_demo else float(db_user.real_cash_balance)
        
        logger.info(f"Wallet initialization complete for user {user_id}: final_balance=₹{final_balance:,.2f}")
        
        return {
            "success": True,
            "data": {
                "wallet_balance": final_balance,
                "formatted_wallet_balance": f"₹{final_balance:,.2f}",
                "is_demo": is_demo
            },
            "message": "Wallet balance initialized/updated successfully"
        }
    except Exception as e:
        logger.error(f"Error initializing wallet: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add-demo-holding")
async def add_demo_holding(
    holding_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a demo holding to portfolio (saved to database)"""
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else (current_user.get("id", 1) if isinstance(current_user, dict) else 1)
        result = await portfolio_allocation_service.add_demo_holding(user_id, holding_data, db)
        return {
            "success": result.get("success", True),
            "data": result,
            "message": result.get("message", "Demo holding added successfully")
        }
    except Exception as e:
        logger.error(f"Error adding demo holding: {e}")
        raise HTTPException(status_code=500, detail=str(e))