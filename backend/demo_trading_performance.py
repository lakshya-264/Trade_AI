"""
Trading Performance Analysis Demo
Shows entry/exit price analysis and P&L calculations for Nifty50 trading signals
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.database import SessionLocal
from services.trading_performance_service import trading_performance_service
from models.trading_performance_models import TradingExecution
from datetime import datetime, timedelta

async def demo_trading_performance():
    """Demonstrate trading performance analysis"""
    
    print("📊 Trading Performance Analysis Demo")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Create sample trading executions for NIFTY_50
        print("\n🔧 Creating Sample Trading Executions...")
        
        sample_trades = [
            {
                'symbol': 'NIFTY_50',
                'signal_type': 'BUY',
                'entry_price': 19500.00,
                'quantity': 100,
                'action': 'ENTRY'
            },
            {
                'symbol': 'NIFTY_50',
                'signal_type': 'SELL',
                'entry_price': 19650.00,
                'quantity': 100,
                'action': 'ENTRY'
            },
            {
                'symbol': 'NIFTY_50',
                'signal_type': 'BUY',
                'entry_price': 19450.00,
                'quantity': 100,
                'action': 'ENTRY'
            }
        ]
        
        executions = []
        for trade_data in sample_trades:
            execution = await trading_performance_service.create_trade_execution(trade_data, db)
            executions.append(execution)
            print(f"  ✅ Created {trade_data['signal_type']} execution at {trade_data['entry_price']}")
        
        # Close some trades with exit prices (some profitable, some losses)
        print("\n📈 Closing Trades with Exit Prices...")
        
        exit_scenarios = [
            (executions[0].id, 19700.00, "TARGET_HIT"),  # Profit: +200 points
            (executions[1].id, 19550.00, "STOP_LOSS"),   # Loss: -100 points  
            (executions[2].id, 19600.00, "MANUAL"),       # Profit: +150 points
        ]
        
        for exec_id, exit_price, reason in exit_scenarios:
            closed_exec = await trading_performance_service.close_trade_execution(
                exec_id, exit_price, db, reason
            )
            print(f"  ✅ Closed trade: {closed_exec.profit_loss} {closed_exec.pnl_percent:.2f}%")
        
        # Analyze entry/exit patterns
        print("\n🔍 Analyzing Entry/Exit Patterns...")
        
        analysis = await trading_performance_service._analyze_entry_exit_patterns(executions)
        
        print(f"  📊 Total Closed Trades: {analysis.get('total_closed_trades', 0)}")
        print(f"  📈 Exits Higher Than Entry: {analysis.get('exits_higher_than_entry', 0)}")
        print(f"  📉 Exits Lower Than Entry: {analysis.get('exits_lower_than_entry', 0)}")
        print(f"  ⚖️  Exits Equal To Entry: {analysis.get('exits_equal_entry', 0)}")
        
        exit_patterns = analysis.get('exit_patterns', {})
        print(f"  🎯 Profitable Exit Rate: {exit_patterns.get('profitable_exit_rate', 0):.1%}")
        print(f"  💸 Loss Exit Rate: {exit_patterns.get('loss_exit_rate', 0):.1%}")
        
        price_stats = analysis.get('price_statistics', {})
        if price_stats:
            print(f"  💰 Average Price Change: {price_stats.get('avg_price_change_percent', 0):.2f}%")
            print(f"  📈 Max Profit: {price_stats.get('max_price_gain', 0):.2f}%")
            print(f"  📉 Max Loss: {price_stats.get('max_price_loss', 0):.2f}%")
        
        # Get comprehensive performance summary
        print("\n📋 Comprehensive Performance Summary...")
        
        summary = await trading_performance_service.get_symbol_performance_summary('NIFTY_50', 30, db)
        
        performance = summary.get('performance_metrics', {})
        if performance:
            print(f"  📊 Total Trades: {performance.get('total_trades', 0)}")
            print(f"  🎯 Win Rate: {performance.get('win_rate', 0):.1%}")
            print(f"  💰 Total P&L: {performance.get('total_pnl_percent', 0):.2f}%")
            print(f"  📈 Profitable Trades: {performance.get('profitable_trades', 0)}")
            print(f"  📉 Losing Trades: {performance.get('losing_trades', 0)}")
        
        # Show recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Performance Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Demonstrate entry/exit price meaning
        print("\n🎓 What Entry/Exit Prices Mean:")
        print("-" * 40)
        print("📈 Exit Price > Entry Price = PROFIT")
        print("   • You bought at 19500, sold at 19700 = +200 points profit")
        print("   • Percentage: ((19700-19500)/19500) * 100 = +1.03%")
        print("")
        print("📉 Exit Price < Entry Price = LOSS") 
        print("   • You sold at 19650, covered at 19550 = -100 points loss")
        print("   • Percentage: ((19550-19650)/19650) * 100 = -0.51%")
        print("")
        print("⚖️  Exit Price ≈ Entry Price = BREAKEVEN")
        print("   • Minimal price change = breakeven trade")
        print("   • Small gains/losses (< 0.1%) considered breakeven")
        
        print("\n🎯 Key Insights from Analysis:")
        print("-" * 40)
        print("✅ System now tracks entry vs exit prices automatically")
        print("✅ Calculates P&L percentage changes accurately")
        print("✅ Identifies profitable vs losing trade patterns")
        print("✅ Provides performance recommendations")
        print("✅ Helps improve trading strategy based on data")
        
    except Exception as e:
        print(f"❌ Demo Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(demo_trading_performance())
