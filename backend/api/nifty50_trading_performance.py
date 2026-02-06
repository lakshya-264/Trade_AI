"""
Nifty50 Trading Performance API
Simple performance metrics for Nifty50 trading signals
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import random

router = APIRouter(prefix="/api/nifty50/performance", tags=["Nifty50 Performance"])

# Sample performance data for demonstration
def generate_sample_performance_data(symbol: str) -> Dict[str, Any]:
    """Generate sample performance data for a symbol"""
    
    # Generate realistic performance metrics
    total_trades = random.randint(10, 50)
    winning_trades = random.randint(int(total_trades * 0.4), int(total_trades * 0.7))
    losing_trades = total_trades - winning_trades
    
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    
    # Generate P&L data
    total_pnl = random.uniform(-5, 15)  # -5% to +15%
    profitable_trades = winning_trades
    losing_trades_count = losing_trades
    
    # Generate average profit/loss
    avg_profit = random.uniform(1, 5) if winning_trades > 0 else 0
    avg_loss = random.uniform(1, 3) if losing_trades > 0 else 0
    
    # Generate entry/exit analysis
    exits_higher = random.randint(int(winning_trades * 0.8), winning_trades)
    exits_lower = losing_trades_count
    exits_equal = total_trades - exits_higher - exits_lower
    
    return {
        "symbol": symbol,
        "performance_metrics": {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl_percent": round(total_pnl, 2),
            "profitable_trades": profitable_trades,
            "losing_trades": losing_trades_count,
            "avg_profit_percent": round(avg_profit, 2),
            "avg_loss_percent": round(avg_loss, 2),
            "max_profit_percent": round(random.uniform(5, 15), 2),
            "max_loss_percent": round(random.uniform(3, 8), 2),
            "sharpe_ratio": round(random.uniform(0.5, 2.5), 2),
            "max_drawdown": round(random.uniform(2, 8), 2),
            "volatility": round(random.uniform(10, 25), 2),
            "avg_holding_period_days": round(random.uniform(1, 7), 1)
        },
        "entry_exit_analysis": {
            "total_closed_trades": total_trades,
            "exits_higher_than_entry": exits_higher,
            "exits_lower_than_entry": exits_lower,
            "exits_equal_to_entry": exits_equal,
            "profitable_exit_rate": round((exits_higher / total_trades) * 100, 2) if total_trades > 0 else 0,
            "loss_exit_rate": round((exits_lower / total_trades) * 100, 2) if total_trades > 0 else 0,
            "breakeven_rate": round((exits_equal / total_trades) * 100, 2) if total_trades > 0 else 0,
            "price_statistics": {
                "avg_price_change_percent": round(random.uniform(-2, 5), 2),
                "max_profit_percent": round(random.uniform(5, 15), 2),
                "max_loss_percent": round(random.uniform(3, 8), 2)
            },
            "time_analysis": {
                "avg_holding_period_hours": round(random.uniform(12, 168), 1),
                "shortest_trade_hours": round(random.uniform(1, 24), 1),
                "longest_trade_hours": round(random.uniform(48, 720), 1)
            },
            "pattern_analysis": {
                "morning_exits": random.randint(int(total_trades * 0.2), int(total_trades * 0.4)),
                "afternoon_exits": random.randint(int(total_trades * 0.3), int(total_trades * 0.5)),
                "end_of_day_exits": random.randint(int(total_trades * 0.1), int(total_trades * 0.3))
            }
        },
        "recent_trades": generate_recent_trades(symbol, min(5, total_trades)),
        "performance_trend": generate_performance_trend(),
        "risk_metrics": {
            "var_95": round(random.uniform(2, 6), 2),
            "cvar_95": round(random.uniform(3, 8), 2),
            "max_consecutive_losses": random.randint(2, 6),
            "recovery_factor": round(random.uniform(1.2, 3.5), 2),
            "profit_factor": round(random.uniform(1.1, 2.8), 2)
        }
    }

def generate_recent_trades(symbol: str, count: int) -> List[Dict[str, Any]]:
    """Generate recent trade data"""
    trades = []
    for i in range(count):
        entry_price = random.uniform(1000, 5000)
        exit_price = entry_price * random.uniform(0.95, 1.08)
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        
        trade = {
            "trade_id": f"{symbol}_{i+1}",
            "entry_price": round(entry_price, 2),
            "exit_price": round(exit_price, 2),
            "pnl_percent": round(pnl_percent, 2),
            "signal_type": random.choice(["BUY", "SELL", "HOLD"]),
            "entry_time": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
            "exit_time": (datetime.now() - timedelta(hours=random.randint(0, 70))).isoformat(),
            "holding_period_hours": round(random.uniform(1, 72), 1),
            "profit_loss": round(pnl_percent > 0, 2)
        }
        trades.append(trade)
    
    return trades

def generate_performance_trend() -> List[Dict[str, Any]]:
    """Generate performance trend data"""
    trend_data = []
    base_value = 100
    
    for i in range(30):  # 30 days trend
        change = random.uniform(-3, 5)
        base_value += change
        base_value = max(50, min(150, base_value))  # Keep between 50 and 150
        
        trend_data.append({
            "date": (datetime.now() - timedelta(days=29-i)).strftime("%Y-%m-%d"),
            "portfolio_value": round(base_value, 2),
            "daily_return": round(change, 2),
            "cumulative_return": round(base_value - 100, 2)
        })
    
    return trend_data

@router.get("/symbol/{symbol}/summary")
async def get_nifty50_performance_summary(
    symbol: str,
    days: int = Query(30, description="Number of days to analyze")
):
    """Get performance summary for a Nifty50 symbol"""
    try:
        # Generate sample performance data
        performance_data = generate_sample_performance_data(symbol)
        
        return {
            "success": True,
            "data": performance_data,
            "message": f"Performance summary for {symbol} over {days} days (sample data)",
            "timestamp": datetime.now().isoformat(),
            "data_source": "SAMPLE_GENERATED"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")

@router.get("/symbol/{symbol}/entry-exit")
async def get_nifty50_entry_exit_analysis(
    symbol: str,
    days: int = Query(30, description="Number of days to analyze")
):
    """Get entry/exit analysis for a Nifty50 symbol"""
    try:
        performance_data = generate_sample_performance_data(symbol)
        
        return {
            "success": True,
            "data": performance_data["entry_exit_analysis"],
            "message": f"Entry/exit analysis for {symbol} over {days} days (sample data)",
            "timestamp": datetime.now().isoformat(),
            "data_source": "SAMPLE_GENERATED"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entry/exit analysis: {str(e)}")

@router.get("/dashboard")
async def get_nifty50_performance_dashboard():
    """Get performance dashboard for multiple Nifty50 symbols"""
    try:
        # Top Nifty50 symbols
        symbols = ["TCS", "RELIANCE", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK"]
        
        dashboard_data = {}
        for symbol in symbols:
            performance_data = generate_sample_performance_data(symbol)
            dashboard_data[symbol] = {
                "total_trades": performance_data["performance_metrics"]["total_trades"],
                "win_rate": performance_data["performance_metrics"]["win_rate"],
                "total_pnl_percent": performance_data["performance_metrics"]["total_pnl_percent"],
                "last_updated": datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "data": {
                "symbols": dashboard_data,
                "summary": {
                    "total_symbols_analyzed": len(symbols),
                    "avg_win_rate": round(sum(data["win_rate"] for data in dashboard_data.values()) / len(symbols), 2),
                    "total_trades": sum(data["total_trades"] for data in dashboard_data.values()),
                    "best_performer": max(dashboard_data.items(), key=lambda x: x[1]["total_pnl_percent"])[0],
                    "worst_performer": min(dashboard_data.items(), key=lambda x: x[1]["total_pnl_percent"])[0]
                }
            },
            "message": "Nifty50 performance dashboard (sample data)",
            "timestamp": datetime.now().isoformat(),
            "data_source": "SAMPLE_GENERATED"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")

@router.get("/market-overview")
async def get_nifty50_market_overview():
    """Get market overview for Nifty50 performance"""
    try:
        # Generate market overview data
        overview_data = {
            "market_sentiment": random.choice(["BULLISH", "BEARISH", "NEUTRAL"]),
            "market_strength": random.uniform(0.3, 0.9),
            "volatility_index": round(random.uniform(10, 30), 2),
            "volume_analysis": {
                "avg_volume": random.randint(1000000, 5000000),
                "volume_trend": random.choice(["INCREASING", "DECREASING", "STABLE"]),
                "volume_change_percent": round(random.uniform(-20, 20), 2)
            },
            "sector_performance": {
                "IT": round(random.uniform(-3, 5), 2),
                "BANKING": round(random.uniform(-2, 4), 2),
                "PHARMA": round(random.uniform(-1, 3), 2),
                "OIL_GAS": round(random.uniform(-4, 6), 2),
                "AUTO": round(random.uniform(-3, 4), 2)
            },
            "top_gainers": [
                {"symbol": "TCS", "change": round(random.uniform(2, 8), 2)},
                {"symbol": "RELIANCE", "change": round(random.uniform(1, 6), 2)},
                {"symbol": "INFY", "change": round(random.uniform(1, 5), 2)}
            ],
            "top_losers": [
                {"symbol": "HDFCBANK", "change": round(random.uniform(-6, -1), 2)},
                {"symbol": "ICICIBANK", "change": round(random.uniform(-5, -1), 2)},
                {"symbol": "KOTAKBANK", "change": round(random.uniform(-4, -1), 2)}
            ]
        }
        
        return {
            "success": True,
            "data": overview_data,
            "message": "Nifty50 market overview (sample data)",
            "timestamp": datetime.now().isoformat(),
            "data_source": "SAMPLE_GENERATED"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market overview: {str(e)}")
