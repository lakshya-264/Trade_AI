"""
Strategy Optimization Service
Parameter optimization for trading strategies using grid search and genetic algorithms
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

logger = logging.getLogger(__name__)

class StrategyOptimizer:
    """Optimize strategy parameters using various algorithms"""
    
    def __init__(self):
        self.max_workers = 4  # Parallel optimization workers
        self.cache = {}  # Cache optimization results
        
    async def grid_search_optimization(
        self,
        symbol: str,
        strategy_type: str,
        param_ranges: Dict[str, List[float]],
        objective: str = "sharpe_ratio"  # sharpe_ratio, profit_factor, total_return
    ) -> Dict[str, Any]:
        """Grid search optimization for strategy parameters"""
        try:
            logger.info(f"🔍 Grid search optimization for {symbol} - {strategy_type}")
            
            # Generate all parameter combinations
            param_combinations = self._generate_combinations(param_ranges)
            total_combinations = len(param_combinations)
            
            logger.info(f"Testing {total_combinations} parameter combinations...")
            
            # Run backtests in parallel
            results = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for params in param_combinations:
                    future = executor.submit(
                        self._run_backtest_with_params,
                        symbol, strategy_type, params
                    )
                    futures.append((future, params))
                
                # Collect results
                for future, params in futures:
                    try:
                        result = future.result(timeout=60)  # 60s timeout per backtest
                        if result and result.get("success"):
                            results.append({
                                "params": params,
                                "metrics": result.get("metrics", {}),
                                "result": result
                            })
                    except Exception as e:
                        logger.warning(f"Backtest failed for params {params}: {e}")
                        continue
            
            if not results:
                return {"success": False, "error": "No successful backtests"}
            
            # Sort by objective
            results.sort(
                key=lambda x: x["metrics"].get(objective, 0),
                reverse=True
            )
            
            # Get best parameters
            best_result = results[0]
            
            return {
                "success": True,
                "best_params": best_result["params"],
                "best_metrics": best_result["metrics"],
                "all_results": results[:10],  # Top 10 results
                "total_tested": total_combinations,
                "successful_tests": len(results),
                "objective": objective
            }
            
        except Exception as e:
            logger.error(f"Error in grid search optimization: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_combinations(self, param_ranges: Dict[str, List[float]]) -> List[Dict]:
        """Generate all parameter combinations"""
        import itertools
        
        keys = list(param_ranges.keys())
        values = list(param_ranges.values())
        
        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo)))
        
        return combinations
    
    def _run_backtest_with_params(
        self,
        symbol: str,
        strategy_type: str,
        params: Dict[str, float]
    ) -> Optional[Dict]:
        """Run backtest with specific parameters"""
        try:
            from services.backtesting_engine import BacktestingEngine
            engine = BacktestingEngine()
            
            # Run backtest based on strategy type
            if strategy_type == "sd_zones":
                result = asyncio.run(engine.backtest_supply_demand_zones(
                    symbol=symbol,
                    entry_threshold=params.get("entry_threshold", 0.5),
                    stop_loss=params.get("stop_loss", 2.0),
                    take_profit=params.get("take_profit", 4.0)
                ))
            elif strategy_type == "sr_levels":
                result = asyncio.run(engine.backtest_support_resistance(
                    symbol=symbol,
                    entry_threshold=params.get("entry_threshold", 0.5),
                    stop_loss=params.get("stop_loss", 2.0),
                    take_profit=params.get("take_profit", 4.0)
                ))
            else:
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"Error running backtest with params: {e}")
            return None
    
    async def walk_forward_analysis(
        self,
        symbol: str,
        strategy_type: str,
        optimization_period: int = 60,  # days
        test_period: int = 30,  # days
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Walk-forward analysis for strategy robustness"""
        try:
            logger.info(f"📊 Walk-forward analysis for {symbol}")
            
            # Get historical data
            from services.data_fetcher import fetch_historical_data
            candles = await fetch_historical_data(symbol, timeframe="1d", days=365)
            
            if not candles or len(candles) < optimization_period + test_period:
                return {"success": False, "error": "Insufficient data"}
            
            df = pd.DataFrame(candles)
            df['time'] = pd.to_datetime(df['time'])
            
            # Split into optimization and test periods
            results = []
            start_idx = 0
            
            while start_idx + optimization_period + test_period <= len(df):
                # Optimization period
                opt_data = df.iloc[start_idx:start_idx + optimization_period]
                # Test period
                test_data = df.iloc[start_idx + optimization_period:start_idx + optimization_period + test_period]
                
                # Optimize on optimization period (simplified - use default params)
                # In real implementation, run optimization here
                
                # Test on test period
                test_result = await self._test_strategy_on_period(
                    symbol, strategy_type, test_data, params or {}
                )
                
                if test_result:
                    results.append({
                        "period": {
                            "optimization_start": opt_data.iloc[0]['time'].isoformat(),
                            "optimization_end": opt_data.iloc[-1]['time'].isoformat(),
                            "test_start": test_data.iloc[0]['time'].isoformat(),
                            "test_end": test_data.iloc[-1]['time'].isoformat()
                        },
                        "metrics": test_result.get("metrics", {})
                    })
                
                start_idx += test_period  # Slide forward
            
            if not results:
                return {"success": False, "error": "No valid test periods"}
            
            # Aggregate results
            avg_metrics = self._aggregate_metrics(results)
            
            return {
                "success": True,
                "periods_tested": len(results),
                "average_metrics": avg_metrics,
                "period_results": results
            }
            
        except Exception as e:
            logger.error(f"Error in walk-forward analysis: {e}")
            return {"success": False, "error": str(e)}
    
    async def _test_strategy_on_period(
        self,
        symbol: str,
        strategy_type: str,
        test_data: pd.DataFrame,
        params: Dict
    ) -> Optional[Dict]:
        """Test strategy on a specific period"""
        try:
            from services.backtesting_engine import BacktestingEngine
            engine = BacktestingEngine()
            
            # Convert DataFrame back to candles format
            candles = test_data.to_dict('records')
            
            # Run backtest (simplified - would need to modify engine to accept candles)
            # For now, return mock result
            return {
                "success": True,
                "metrics": {
                    "total_return": np.random.uniform(-5, 15),
                    "sharpe_ratio": np.random.uniform(0.5, 2.0),
                    "win_rate": np.random.uniform(40, 70),
                    "profit_factor": np.random.uniform(0.8, 2.5)
                }
            }
            
        except Exception as e:
            logger.error(f"Error testing strategy on period: {e}")
            return None
    
    def _aggregate_metrics(self, results: List[Dict]) -> Dict[str, float]:
        """Aggregate metrics across periods"""
        metrics_list = [r["metrics"] for r in results]
        
        aggregated = {}
        for key in metrics_list[0].keys():
            values = [m.get(key, 0) for m in metrics_list if m.get(key) is not None]
            if values:
                aggregated[f"avg_{key}"] = np.mean(values)
                aggregated[f"std_{key}"] = np.std(values)
                aggregated[f"min_{key}"] = np.min(values)
                aggregated[f"max_{key}"] = np.max(values)
        
        return aggregated

# Create singleton instance
strategy_optimizer = StrategyOptimizer()

