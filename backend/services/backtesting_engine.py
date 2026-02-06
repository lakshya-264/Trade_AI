"""
Backtesting Engine
Analyzes historical performance of trading strategies
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from services.supply_demand import SupplyDemandService
from services.support_resistance import SupportResistanceService

logger = logging.getLogger(__name__)

class BacktestingEngine:
    """Engine for backtesting trading strategies"""
    
    def __init__(self):
        self.initial_capital = 100000  # Starting with 1 lakh
        self.position_size_percent = 10  # 10% per trade
        self.sd_service = SupplyDemandService()
        self.sr_service = SupportResistanceService()
    
    async def backtest_supply_demand_zones(
        self,
        symbol: str,
        entry_threshold: float = 0.5,
        stop_loss: float = 2.0,
        take_profit: float = 4.0
    ) -> Dict:
        """
        Backtest Supply & Demand zone strategy
        
        Entry Rules:
        - Enter long when price touches demand zone (within threshold %)
        - Enter short when price touches supply zone (within threshold %)
        
        Exit Rules:
        - Stop loss at X% from entry
        - Take profit at Y% from entry
        """
        try:
            logger.info(f"🧪 Backtesting S&D zones for {symbol}")
            
            # Get historical data (last 6 months for testing)
            from services.data_fetcher import fetch_historical_data
            candles = await fetch_historical_data(symbol, timeframe="1d", days=180)
            
            if not candles or len(candles) < 50:
                return {
                    'success': False,
                    'error': 'Insufficient historical data'
                }
            
            # Analyze S&D zones on historical data
            sd_result = self.sd_service.analyze_supply_demand(candles)
            
            if not sd_result.get('success') or not sd_result.get('data'):
                return {
                    'success': False,
                    'error': 'Failed to detect S&D zones'
                }
            
            zones = sd_result['data'].get('zones', [])
            
            # Run backtest simulation
            trades = []
            capital = self.initial_capital
            equity_curve = [{'date': candles[0]['time'], 'equity': capital}]
            
            # Convert candles to DataFrame for easier processing
            df = pd.DataFrame(candles)
            
            for i in range(50, len(df)):  # Start after enough data for zones
                current_price = df.loc[i, 'close']
                current_time = df.loc[i, 'time']
                
                # Check each zone for potential entry
                for zone in zones:
                    if zone['type'] == 'demand':
                        # Long entry if price in demand zone
                        if zone['bottom'] <= current_price <= zone['top']:
                            # Simulate trade
                            entry_price = current_price
                            sl_price = entry_price * (1 - stop_loss / 100)
                            tp_price = entry_price * (1 + take_profit / 100)
                            
                            # Look forward to see outcome
                            exit_result = self._simulate_trade_exit(
                                df, i + 1, sl_price, tp_price, 'long'
                            )
                            
                            if exit_result:
                                trade = {
                                    'entry_time': current_time,
                                    'entry_price': entry_price,
                                    'exit_time': exit_result['exit_time'],
                                    'exit_price': exit_result['exit_price'],
                                    'direction': 'long',
                                    'result': exit_result['result'],
                                    'pnl_percent': exit_result['pnl_percent'],
                                    'zone_type': 'demand'
                                }
                                
                                trades.append(trade)
                                
                                # Update capital
                                position_size = capital * (self.position_size_percent / 100)
                                pnl = position_size * (exit_result['pnl_percent'] / 100)
                                capital += pnl
                                
                                equity_curve.append({
                                    'date': exit_result['exit_time'],
                                    'equity': capital
                                })
                    
                    elif zone['type'] == 'supply':
                        # Short entry if price in supply zone
                        if zone['bottom'] <= current_price <= zone['top']:
                            entry_price = current_price
                            sl_price = entry_price * (1 + stop_loss / 100)
                            tp_price = entry_price * (1 - take_profit / 100)
                            
                            exit_result = self._simulate_trade_exit(
                                df, i + 1, sl_price, tp_price, 'short'
                            )
                            
                            if exit_result:
                                trade = {
                                    'entry_time': current_time,
                                    'entry_price': entry_price,
                                    'exit_time': exit_result['exit_time'],
                                    'exit_price': exit_result['exit_price'],
                                    'direction': 'short',
                                    'result': exit_result['result'],
                                    'pnl_percent': exit_result['pnl_percent'],
                                    'zone_type': 'supply'
                                }
                                
                                trades.append(trade)
                                
                                position_size = capital * (self.position_size_percent / 100)
                                pnl = position_size * (exit_result['pnl_percent'] / 100)
                                capital += pnl
                                
                                equity_curve.append({
                                    'date': exit_result['exit_time'],
                                    'equity': capital
                                })
            
            # Calculate metrics
            basic_metrics = self._calculate_metrics(trades, self.initial_capital, capital)
            advanced_metrics = self.calculate_advanced_metrics(trades, equity_curve)
            
            # Merge metrics
            metrics = {**basic_metrics, **advanced_metrics}
            
            logger.info(f"✅ Backtest complete: {len(trades)} trades, Win Rate: {metrics.get('win_rate', 0):.1f}%")
            
            return {
                'success': True,
                'metrics': metrics,
                'trades': trades[-50:],  # Return last 50 trades
                'equity_curve': equity_curve
            }
            
        except Exception as e:
            logger.error(f"Error in S&D backtest: {e}")
            return {'success': False, 'error': str(e)}
    
    async def backtest_support_resistance(
        self,
        symbol: str,
        entry_threshold: float = 0.5,
        stop_loss: float = 2.0,
        take_profit: float = 4.0
    ) -> Dict:
        """Backtest Support & Resistance level strategy"""
        try:
            logger.info(f"🧪 Backtesting S&R levels for {symbol}")
            
            from services.data_fetcher import fetch_historical_data
            candles = await fetch_historical_data(symbol, timeframe="1d", days=180)
            
            if not candles or len(candles) < 50:
                return {'success': False, 'error': 'Insufficient data'}
            
            # Analyze S&R levels
            sr_result = self.sr_service.analyze_support_resistance(candles)
            
            if not sr_result.get('success') or not sr_result.get('data'):
                return {'success': False, 'error': 'Failed to detect S&R levels'}
            
            levels = sr_result['data'].get('levels', [])
            
            trades = []
            capital = self.initial_capital
            equity_curve = [{'date': candles[0]['time'], 'equity': capital}]
            
            df = pd.DataFrame(candles)
            
            for i in range(50, len(df)):
                current_price = df.loc[i, 'close']
                current_time = df.loc[i, 'time']
                
                # Check levels for entry opportunities
                for level in levels:
                    level_price = level['price']
                    threshold_price = level_price * (entry_threshold / 100)
                    
                    # Support level - potential long
                    if level['type'] == 'support':
                        if abs(current_price - level_price) <= threshold_price:
                            entry_price = current_price
                            sl_price = entry_price * (1 - stop_loss / 100)
                            tp_price = entry_price * (1 + take_profit / 100)
                            
                            exit_result = self._simulate_trade_exit(
                                df, i + 1, sl_price, tp_price, 'long'
                            )
                            
                            if exit_result:
                                position_size = capital * (self.position_size_percent / 100)
                                pnl = position_size * (exit_result['pnl_percent'] / 100)
                                capital += pnl
                                
                                trades.append({
                                    'entry_time': current_time,
                                    'entry_price': entry_price,
                                    'exit_time': exit_result['exit_time'],
                                    'exit_price': exit_result['exit_price'],
                                    'direction': 'long',
                                    'result': exit_result['result'],
                                    'pnl_percent': exit_result['pnl_percent'],
                                    'level_type': 'support'
                                })
                                
                                equity_curve.append({
                                    'date': exit_result['exit_time'],
                                    'equity': capital
                                })
                    
                    # Resistance level - potential short
                    elif level['type'] == 'resistance':
                        if abs(current_price - level_price) <= threshold_price:
                            entry_price = current_price
                            sl_price = entry_price * (1 + stop_loss / 100)
                            tp_price = entry_price * (1 - take_profit / 100)
                            
                            exit_result = self._simulate_trade_exit(
                                df, i + 1, sl_price, tp_price, 'short'
                            )
                            
                            if exit_result:
                                position_size = capital * (self.position_size_percent / 100)
                                pnl = position_size * (exit_result['pnl_percent'] / 100)
                                capital += pnl
                                
                                trades.append({
                                    'entry_time': current_time,
                                    'entry_price': entry_price,
                                    'exit_time': exit_result['exit_time'],
                                    'exit_price': exit_result['exit_price'],
                                    'direction': 'short',
                                    'result': exit_result['result'],
                                    'pnl_percent': exit_result['pnl_percent'],
                                    'level_type': 'resistance'
                                })
                                
                                equity_curve.append({
                                    'date': exit_result['exit_time'],
                                    'equity': capital
                                })
            
            metrics = self._calculate_metrics(trades, self.initial_capital, capital)
            
            return {
                'success': True,
                'metrics': metrics,
                'trades': trades[-50:],
                'equity_curve': equity_curve
            }
            
        except Exception as e:
            logger.error(f"Error in S&R backtest: {e}")
            return {'success': False, 'error': str(e)}
    
    async def backtest_structure_breaks(
        self,
        symbol: str,
        stop_loss: float = 2.0,
        take_profit: float = 4.0
    ) -> Dict:
        """Backtest market structure break strategy (BOS/CHoCH)"""
        try:
            logger.info(f"🧪 Backtesting structure breaks for {symbol}")
            
            # Simple placeholder for now - full implementation later
            return {
                'success': True,
                'metrics': {
                    'total_trades': 0,
                    'win_rate': 0,
                    'profit_factor': 0,
                    'message': 'Structure break backtesting coming soon'
                },
                'trades': [],
                'equity_curve': []
            }
            
        except Exception as e:
            logger.error(f"Error in structure break backtest: {e}")
            return {'success': False, 'error': str(e)}
    
    async def analyze_zone_success_rate(
        self,
        symbol: str,
        timeframe: str = "1d",
        lookback_days: int = 90
    ) -> Dict:
        """Calculate success rate of S&D zones"""
        try:
            from services.data_fetcher import fetch_historical_data
            candles = await fetch_historical_data(symbol, timeframe=timeframe, days=lookback_days)
            
            if not candles or len(candles) < 50:
                return {'error': 'Insufficient data'}
            
            sd_result = self.sd_service.analyze_supply_demand(candles)
            zones = sd_result.get('data', {}).get('zones', [])
            
            demand_touches = 0
            demand_bounces = 0
            supply_touches = 0
            supply_rejections = 0
            
            df = pd.DataFrame(candles)
            
            for zone in zones:
                for i in range(len(df)):
                    low = df.loc[i, 'low']
                    high = df.loc[i, 'high']
                    close = df.loc[i, 'close']
                    
                    # Check if price touched zone
                    if zone['type'] == 'demand':
                        if low <= zone['top'] and high >= zone['bottom']:
                            demand_touches += 1
                            # Check if it bounced (closed higher)
                            if i + 5 < len(df):  # Look 5 candles ahead
                                future_high = df.loc[i:i+5, 'high'].max()
                                bounce_percent = ((future_high - close) / close) * 100
                                if bounce_percent >= 1.0:  # 1% bounce = success
                                    demand_bounces += 1
                    
                    elif zone['type'] == 'supply':
                        if low <= zone['top'] and high >= zone['bottom']:
                            supply_touches += 1
                            # Check if it rejected (closed lower)
                            if i + 5 < len(df):
                                future_low = df.loc[i:i+5, 'low'].min()
                                rejection_percent = ((close - future_low) / close) * 100
                                if rejection_percent >= 1.0:  # 1% rejection = success
                                    supply_rejections += 1
            
            demand_success_rate = (demand_bounces / demand_touches * 100) if demand_touches > 0 else 0
            supply_success_rate = (supply_rejections / supply_touches * 100) if supply_touches > 0 else 0
            
            return {
                'demand_zones': {
                    'total_touches': demand_touches,
                    'successful_bounces': demand_bounces,
                    'success_rate': round(demand_success_rate, 2)
                },
                'supply_zones': {
                    'total_touches': supply_touches,
                    'successful_rejections': supply_rejections,
                    'success_rate': round(supply_success_rate, 2)
                },
                'overall_success_rate': round((demand_success_rate + supply_success_rate) / 2, 2)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing zone success rate: {e}")
            return {'error': str(e)}
    
    async def analyze_pattern_winrate(
        self,
        symbol: str,
        pattern_type: str,
        lookback_days: int = 90
    ) -> Dict:
        """Calculate win rate for specific patterns"""
        # Placeholder for now - full implementation later
        return {
            'pattern': pattern_type,
            'occurrences': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'message': 'Pattern analysis coming soon'
        }
    
    def _simulate_trade_exit(
        self,
        df: pd.DataFrame,
        start_idx: int,
        stop_loss: float,
        take_profit: float,
        direction: str,
        max_bars: int = 20
    ) -> Optional[Dict]:
        """Simulate trade exit based on SL/TP"""
        for i in range(start_idx, min(start_idx + max_bars, len(df))):
            low = df.loc[i, 'low']
            high = df.loc[i, 'high']
            close = df.loc[i, 'close']
            time = df.loc[i, 'time']
            
            if direction == 'long':
                # Check stop loss
                if low <= stop_loss:
                    return {
                        'exit_time': time,
                        'exit_price': stop_loss,
                        'result': 'loss',
                        'pnl_percent': -abs(((stop_loss - df.loc[start_idx-1, 'close']) / df.loc[start_idx-1, 'close']) * 100)
                    }
                # Check take profit
                if high >= take_profit:
                    return {
                        'exit_time': time,
                        'exit_price': take_profit,
                        'result': 'win',
                        'pnl_percent': ((take_profit - df.loc[start_idx-1, 'close']) / df.loc[start_idx-1, 'close']) * 100
                    }
            
            elif direction == 'short':
                # Check stop loss
                if high >= stop_loss:
                    return {
                        'exit_time': time,
                        'exit_price': stop_loss,
                        'result': 'loss',
                        'pnl_percent': -abs(((df.loc[start_idx-1, 'close'] - stop_loss) / df.loc[start_idx-1, 'close']) * 100)
                    }
                # Check take profit
                if low <= take_profit:
                    return {
                        'exit_time': time,
                        'exit_price': take_profit,
                        'result': 'win',
                        'pnl_percent': ((df.loc[start_idx-1, 'close'] - take_profit) / df.loc[start_idx-1, 'close']) * 100
                    }
        
        # No exit within max_bars - close at current price
        final_price = df.loc[min(start_idx + max_bars - 1, len(df) - 1), 'close']
        entry_price = df.loc[start_idx - 1, 'close']
        
        if direction == 'long':
            pnl = ((final_price - entry_price) / entry_price) * 100
        else:
            pnl = ((entry_price - final_price) / entry_price) * 100
        
        return {
            'exit_time': df.loc[min(start_idx + max_bars - 1, len(df) - 1), 'time'],
            'exit_price': final_price,
            'result': 'win' if pnl > 0 else 'loss',
            'pnl_percent': pnl
        }
    
    def _calculate_metrics(self, trades: List[Dict], initial_capital: float, final_capital: float) -> Dict:
        """Calculate comprehensive performance metrics from trades"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'total_return_percent': 0,
                'max_drawdown': 0,
                'avg_drawdown': 0,
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'calmar_ratio': 0,
                'expectancy': 0,
                'recovery_factor': 0
            }
        
        wins = [t for t in trades if t['result'] == 'win']
        losses = [t for t in trades if t['result'] == 'loss']
        
        win_pnls = [t['pnl_percent'] for t in wins] if wins else [0]
        loss_pnls = [abs(t['pnl_percent']) for t in losses] if losses else [0]
        
        total_win_pnl = sum(win_pnls)
        total_loss_pnl = sum(loss_pnls)
        
        # Calculate drawdown metrics
        equity_curve = [initial_capital]
        for trade in trades:
            position_size = equity_curve[-1] * (self.position_size_percent / 100)
            pnl = position_size * (trade['pnl_percent'] / 100)
            equity_curve.append(equity_curve[-1] + pnl)
        
        max_dd, avg_dd, dd_duration = self._calculate_drawdown(equity_curve)
        
        # Calculate risk-adjusted returns
        all_pnls = [t['pnl_percent'] for t in trades]
        sharpe = self._calculate_sharpe_ratio(all_pnls)
        sortino = self._calculate_sortino_ratio(all_pnls)
        
        # Calculate other advanced metrics
        net_profit = final_capital - initial_capital
        calmar = self._calculate_calmar_ratio(net_profit / initial_capital * 100, max_dd)
        expectancy = self._calculate_expectancy(wins, losses)
        recovery = self._calculate_recovery_factor(net_profit, max_dd, initial_capital)
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': round((len(wins) / len(trades)) * 100, 2),
            'avg_win': round(sum(win_pnls) / len(wins), 2) if wins else 0,
            'avg_loss': round(sum(loss_pnls) / len(losses), 2) if losses else 0,
            'profit_factor': round(total_win_pnl / total_loss_pnl, 2) if total_loss_pnl > 0 else 0,
            'total_return_percent': round(((final_capital - initial_capital) / initial_capital) * 100, 2),
            'final_capital': round(final_capital, 2),
            'max_consecutive_wins': self._max_consecutive(wins),
            'max_consecutive_losses': self._max_consecutive(losses),
            # Advanced metrics
            'max_drawdown': round(max_dd, 2),
            'avg_drawdown': round(avg_dd, 2),
            'max_dd_duration': dd_duration,
            'sharpe_ratio': round(sharpe, 2),
            'sortino_ratio': round(sortino, 2),
            'calmar_ratio': round(calmar, 2),
            'expectancy': round(expectancy, 2),
            'recovery_factor': round(recovery, 2)
        }
    
    def _max_consecutive(self, trades: List[Dict]) -> int:
        """Calculate maximum consecutive wins/losses"""
        if not trades:
            return 0
        
        max_consecutive = 1
        current_consecutive = 1
        
        for i in range(1, len(trades)):
            if trades[i]['result'] == trades[i-1]['result']:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
        
        return max_consecutive
    
    def _calculate_drawdown(self, equity_curve: List[float]) -> tuple:
        """
        Calculate maximum drawdown, average drawdown, and max drawdown duration
        
        Returns:
            (max_drawdown_percent, avg_drawdown_percent, max_duration_days)
        """
        if len(equity_curve) < 2:
            return 0.0, 0.0, 0
        
        equity_array = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdowns = (equity_array - running_max) / running_max * 100
        
        # Max drawdown
        max_dd = abs(drawdowns.min())
        
        # Average drawdown (only count actual drawdowns)
        dd_values = drawdowns[drawdowns < 0]
        avg_dd = abs(dd_values.mean()) if len(dd_values) > 0 else 0.0
        
        # Max drawdown duration (count consecutive negative periods)
        max_duration = 0
        current_duration = 0
        for dd in drawdowns:
            if dd < 0:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0
        
        return max_dd, avg_dd, max_duration
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe Ratio (risk-adjusted return)
        
        Sharpe Ratio = (Mean Return - Risk Free Rate) / Std Dev of Returns
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        mean_return = returns_array.mean()
        std_return = returns_array.std()
        
        if std_return == 0:
            return 0.0
        
        # Annualize (assuming 252 trading days)
        sharpe = (mean_return - risk_free_rate) / std_return * np.sqrt(252)
        
        return sharpe
    
    def _calculate_sortino_ratio(self, returns: List[float], risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sortino Ratio (downside risk-adjusted return)
        
        Sortino Ratio = (Mean Return - Risk Free Rate) / Downside Std Dev
        """
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        mean_return = returns_array.mean()
        
        # Only consider negative returns for downside deviation
        negative_returns = returns_array[returns_array < 0]
        
        if len(negative_returns) == 0:
            return 0.0  # No downside risk
        
        downside_std = negative_returns.std()
        
        if downside_std == 0:
            return 0.0
        
        # Annualize
        sortino = (mean_return - risk_free_rate) / downside_std * np.sqrt(252)
        
        return sortino
    
    def _calculate_calmar_ratio(self, total_return_percent: float, max_drawdown_percent: float) -> float:
        """
        Calculate Calmar Ratio (return / max drawdown)
        
        Higher is better. Shows return per unit of risk.
        """
        if max_drawdown_percent == 0:
            return 0.0
        
        calmar = total_return_percent / max_drawdown_percent
        
        return calmar
    
    def _calculate_expectancy(self, wins: List[Dict], losses: List[Dict]) -> float:
        """
        Calculate Expectancy (expected profit per trade)
        
        Expectancy = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
        """
        total_trades = len(wins) + len(losses)
        
        if total_trades == 0:
            return 0.0
        
        win_rate = len(wins) / total_trades
        loss_rate = len(losses) / total_trades
        
        avg_win = sum([w['pnl_percent'] for w in wins]) / len(wins) if wins else 0
        avg_loss = sum([abs(l['pnl_percent']) for l in losses]) / len(losses) if losses else 0
        
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        return expectancy
    
    def _calculate_recovery_factor(self, net_profit: float, max_drawdown_percent: float, initial_capital: float) -> float:
        """
        Calculate Recovery Factor (net profit / max drawdown)
        
        Shows how many times profit covers max drawdown.
        Higher is better.
        """
        if max_drawdown_percent == 0:
            return 0.0
        
        max_dd_dollars = initial_capital * (max_drawdown_percent / 100)
        
        if max_dd_dollars == 0:
            return 0.0
        
        recovery = net_profit / max_dd_dollars
        
        return recovery

