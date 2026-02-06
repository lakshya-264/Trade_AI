"""
Smart Money Volume Activity Service

Approximates the TradingView Pine Script logic by:
- Fetching lower timeframe (LTF) OHLCV data for a given symbol
- Computing Z-scores on LTF volume over a sliding window (z_len)
- Detecting significant events where |Z| >= threshold
- Classifying events into Retail (class 1) vs Smart (class 2) based on proximity to current bar body
- Aggregating per-bar bubble (strongest |Z|), levels list, and P/L volume totals

Notes:
- This service returns data for the current higher-timeframe bar using LTF aggregation.
- For data access, it relies on enhanced_chart_service to fetch candlesticks.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging
import math

try:
    # Prefer local service import path used in comprehensive_trading
    from services.enhanced_chart_service import enhanced_chart_service
except Exception:  # pragma: no cover - fallback if path differs
    enhanced_chart_service = None  # type: ignore

logger = logging.getLogger(__name__)


class SmartMoneyVolumeService:
    def __init__(self) -> None:
        if enhanced_chart_service is None:
            logger.warning("enhanced_chart_service not available; SmartMoneyVolumeService will be limited")

    async def analyze_volume_activity(
        self,
        *,
        symbol: str,
        timeframe: str = "1D",
        lower_timeframe: str = "5m",
        z_len: int = 50,
        threshold_abs: float = 2.0,
        who: str = "Both",
    ) -> Dict[str, Any]:
        """Analyze lower-timeframe volume events and map to higher-timeframe bar.

        Returns a structure suitable for frontend rendering with levels, bubble info,
        and P/L volume aggregates.
        """
        try:
            ltf = lower_timeframe
            # Fetch LTF candles for the same period as the current HTF context
            # We over-fetch to ensure at least z_len window
            period = max(200, z_len * 3)
            ltf_data = await self._get_candles(symbol=symbol, timeframe=ltf, period=period)
            if not ltf_data or not ltf_data.get("candlesticks"):
                return self._empty_result(symbol, timeframe, ltf)

            ltf_candles = ltf_data["candlesticks"]

            # Compute Z-scores on volume
            volumes = [float(c.get("volume", 0)) for c in ltf_candles]
            if len(volumes) < z_len:
                return self._empty_result(symbol, timeframe, ltf)

            def mean_std(vals: List[float]) -> Tuple[float, float]:
                if not vals:
                    return 0.0, 0.0
                m = sum(vals) / len(vals)
                var = sum((v - m) ** 2 for v in vals) / max(1, len(vals) - 1)
                return m, var ** 0.5

            window = volumes[-z_len:]
            m, s = mean_std(window)
            # Identify indices whose volume is significant vs window stats
            significant_indices: List[int] = []
            if s > 0:
                for idx, vol in enumerate(volumes[-z_len:]):
                    z = (vol - m) / s
                    if abs(z) >= threshold_abs:
                        # map back to full array index
                        significant_indices.append(len(volumes) - z_len + idx)

            # Build current HTF body from last HTF candle to classify levels
            htf = await self._get_candles(symbol=symbol, timeframe=timeframe, period=3)
            body_min = body_max = None
            if htf and htf.get("candlesticks"):
                last = htf["candlesticks"][-1]
                o = float(last.get("open", 0.0))
                c = float(last.get("close", 0.0))
                body_min = min(o, c)
                body_max = max(o, c)

            # Aggregate events
            levels: List[Dict[str, Any]] = []
            bar_max_abs_z = None
            bar_bubble: Optional[Dict[str, Any]] = None
            retail_profit_vol = retail_loss_vol = 0.0
            smart_profit_vol = smart_loss_vol = 0.0

            for i in significant_indices:
                cndl = ltf_candles[i]
                o = float(cndl.get("open", 0.0))
                cl = float(cndl.get("close", 0.0))
                v = float(cndl.get("volume", 0.0))
                is_bull = cl > o
                typ = 1 if is_bull else -1
                lvl_price = cl

                z_val = 0.0
                if s > 0:
                    z_val = (v - m) / s

                # Classify class: 1 Retail (at close), 2 Smart (inside body)
                cls = 1
                if body_min is not None and body_max is not None:
                    is_at_close = lvl_price == c
                    is_in_body = body_min < lvl_price < body_max
                    cls = 1 if is_at_close else (2 if is_in_body else 1)

                # who filter
                class_allowed = (
                    who == "Both"
                    or (who == "Retail" and cls == 1)
                    or (who == "Smart Money" and cls == 2)
                )
                if not class_allowed:
                    continue

                level_item = {
                    "price": lvl_price,
                    "type": typ,  # 1 bull, -1 bear
                    "class": cls,  # 1 retail, 2 smart
                    "volume": v,
                    "z": z_val,
                    "timestamp": cndl.get("timestamp") or cndl.get("time") or datetime.utcnow().isoformat(),
                }
                levels.append(level_item)

                # Track per-bar bubble (max |z|)
                abs_z = abs(z_val)
                if bar_max_abs_z is None or abs_z > bar_max_abs_z:
                    bar_max_abs_z = abs_z
                    bar_bubble = {
                        "price": lvl_price,
                        "dir": 1 if is_bull else -1,
                        "class": cls,
                        "abs_z": abs_z,
                    }

                # P/L aggregates relative to last HTF close price
                if body_min is not None and body_max is not None:
                    in_profit = (typ == 1 and c >= lvl_price) or (typ == -1 and c <= lvl_price)
                    if cls == 1:
                        if in_profit:
                            retail_profit_vol += v
                        else:
                            retail_loss_vol += v
                    elif cls == 2:
                        if in_profit:
                            smart_profit_vol += v
                        else:
                            smart_loss_vol += v

            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "lower_timeframe": ltf,
                "levels": levels,
                "bubble": bar_bubble,
                "pl": {
                    "retail_profit": retail_profit_vol,
                    "retail_loss": retail_loss_vol,
                    "smart_profit": smart_profit_vol,
                    "smart_loss": smart_loss_vol,
                },
                "count": len(levels),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error analyzing smart money volume for {symbol}: {e}")
            return {"success": False, "error": str(e)}

    async def _get_candles(self, *, symbol: str, timeframe: str, period: int) -> Dict[str, Any]:
        if enhanced_chart_service is None:
            return {}
        data = await enhanced_chart_service.get_candlestick_data(
            symbol=symbol,
            timeframe=timeframe,
            period=period,
        )
        # Some services return under 'data'
        if isinstance(data, dict) and "candlesticks" not in data and "data" in data:
            inner = data.get("data")
            if isinstance(inner, dict) and "candlesticks" in inner:
                return inner
        return data or {}

    def _empty_result(self, symbol: str, timeframe: str, ltf: str) -> Dict[str, Any]:
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "lower_timeframe": ltf,
            "levels": [],
            "bubble": None,
            "pl": {"retail_profit": 0.0, "retail_loss": 0.0, "smart_profit": 0.0, "smart_loss": 0.0},
            "count": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Singleton
smart_money_volume_service = SmartMoneyVolumeService()


