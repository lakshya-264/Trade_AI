"""
Multi-Timeframe Analysis API Routes
Provides parallel analysis across multiple timeframes with alignment indicators
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Timeframe configuration with optimal periods
TIMEFRAME_CONFIG = {
    # Intraday
    '1m': {'interval': '1m', 'period': '7d', 'label': '1 Minute', 'weight': 1},
    '5m': {'interval': '5m', 'period': '1mo', 'label': '5 Minutes', 'weight': 2},
    '15m': {'interval': '15m', 'period': '1mo', 'label': '15 Minutes', 'weight': 3},
    '30m': {'interval': '30m', 'period': '3mo', 'label': '30 Minutes', 'weight': 4},
    '1H': {'interval': '1h', 'period': '3mo', 'label': '1 Hour', 'weight': 5},
    '4H': {'interval': '1h', 'period': '6mo', 'label': '4 Hours', 'weight': 6},
    # Daily+
    '1D': {'interval': '1d', 'period': '1y', 'label': '1 Day', 'weight': 7},
    '1W': {'interval': '1wk', 'period': '2y', 'label': '1 Week', 'weight': 8},
    '1M': {'interval': '1mo', 'period': '5y', 'label': '1 Month', 'weight': 9},
}

async def fetch_timeframe_data(symbol: str, timeframe: str, limit: int = 500):
    """Fetch candle data for a specific timeframe"""
    try:
        from core.yahoo_finance_scraper import yahoo_finance_scraper
        
        if timeframe not in TIMEFRAME_CONFIG:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        config = TIMEFRAME_CONFIG[timeframe]
        logger.info(f"📊 Fetching {timeframe} data for {symbol}")
        
        candles = await yahoo_finance_scraper.get_historical_candles(
            symbol=symbol,
            interval=config['interval'],
            range_period=config['period']
        )
        
        # Limit to requested number of candles
        if candles and len(candles) > limit:
            candles = candles[-limit:]
        
        # Add 4H resampling if needed
        if timeframe == '4H' and candles:
            candles = resample_to_4h(candles)
        
        return candles or []
        
    except Exception as e:
        logger.error(f"Error fetching {timeframe} data for {symbol}: {e}")
        return []


def resample_to_4h(hourly_candles: List[Dict]) -> List[Dict]:
    """Resample 1H candles to 4H"""
    if not hourly_candles or len(hourly_candles) < 4:
        return hourly_candles
    
    resampled = []
    for i in range(0, len(hourly_candles), 4):
        chunk = hourly_candles[i:i+4]
        if len(chunk) > 0:
            resampled.append({
                'time': chunk[-1]['time'],  # Use last candle's time
                'open': chunk[0]['open'],
                'high': max(c['high'] for c in chunk),
                'low': min(c['low'] for c in chunk),
                'close': chunk[-1]['close'],
                'volume': sum(c['volume'] for c in chunk)
            })
    
    return resampled


async def analyze_timeframe_structure(symbol: str, timeframe: str, candles: List[Dict]) -> Dict:
    """Analyze market structure for a specific timeframe"""
    try:
        from api.routes.market_structure import detect_structure
        
        # Convert to required format
        candle_data = {
            'symbol': symbol,
            'data': candles
        }
        
        # Run structure analysis
        structure = await detect_structure(candle_data)
        
        # Determine trend from structure
        trend = determine_trend_from_structure(structure)
        
        return {
            'timeframe': timeframe,
            'structure': structure,
            'trend': trend['direction'],
            'confidence': trend['confidence'],
            'last_bos': get_last_bos(structure)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing structure for {timeframe}: {e}")
        return {
            'timeframe': timeframe,
            'structure': {},
            'trend': 'neutral',
            'confidence': 0.0,
            'last_bos': None
        }


def determine_trend_from_structure(structure: Dict) -> Dict:
    """Determine trend direction and confidence from market structure"""
    bos_events = structure.get('bos_events', [])
    choch_events = structure.get('choch_events', [])
    
    if not bos_events and not choch_events:
        return {'direction': 'neutral', 'confidence': 0.0}
    
    # Get recent events (last 5)
    recent_bos = bos_events[-5:] if len(bos_events) >= 5 else bos_events
    recent_choch = choch_events[-3:] if len(choch_events) >= 3 else choch_events
    
    # Count bullish vs bearish
    bullish_count = sum(1 for event in recent_bos if event.get('direction') == 'bullish')
    bearish_count = sum(1 for event in recent_bos if event.get('direction') == 'bearish')
    
    # CHoCH events indicate trend change
    if recent_choch:
        last_choch = recent_choch[-1]
        direction = last_choch.get('direction', 'neutral')
        confidence = 0.65  # Medium confidence on trend change
    elif bullish_count > bearish_count:
        direction = 'bullish'
        confidence = min(0.9, 0.5 + (bullish_count - bearish_count) * 0.1)
    elif bearish_count > bullish_count:
        direction = 'bearish'
        confidence = min(0.9, 0.5 + (bearish_count - bullish_count) * 0.1)
    else:
        direction = 'neutral'
        confidence = 0.5
    
    return {
        'direction': direction,
        'confidence': round(confidence, 2)
    }


def get_last_bos(structure: Dict) -> Optional[str]:
    """Get direction of last Break of Structure"""
    bos_events = structure.get('bos_events', [])
    if bos_events:
        return bos_events[-1].get('direction')
    return None


def calculate_timeframe_alignment(analyses: Dict[str, Dict]) -> Dict:
    """Calculate overall alignment across timeframes"""
    if not analyses:
        return {
            'verdict': 'NEUTRAL',
            'confidence': 0.0,
            'alignment_pct': 0,
            'bullish_count': 0,
            'total_count': 0,
            'agreement': 'No data',
            'recommendation': 'Unable to analyze'
        }
    
    # Count trends
    bullish_count = 0
    bearish_count = 0
    total_count = len(analyses)
    weighted_score = 0
    total_weight = 0
    
    for tf, data in analyses.items():
        trend = data.get('trend', 'neutral')
        confidence = data.get('confidence', 0.0)
        weight = TIMEFRAME_CONFIG.get(tf, {}).get('weight', 5)
        
        if trend == 'bullish':
            bullish_count += 1
            weighted_score += confidence * weight
        elif trend == 'bearish':
            bearish_count += 1
            weighted_score -= confidence * weight
        
        total_weight += weight
    
    # Calculate alignment percentage
    dominant_count = max(bullish_count, bearish_count)
    alignment_pct = (dominant_count / total_count * 100) if total_count > 0 else 0
    
    # Determine verdict
    if bullish_count > bearish_count:
        if alignment_pct >= 75:
            verdict = 'STRONG BULLISH'
        else:
            verdict = 'BULLISH'
        agreement = f"{bullish_count}/{total_count} timeframes bullish"
    elif bearish_count > bullish_count:
        if alignment_pct >= 75:
            verdict = 'STRONG BEARISH'
        else:
            verdict = 'BEARISH'
        agreement = f"{bearish_count}/{total_count} timeframes bearish"
    else:
        verdict = 'NEUTRAL'
        agreement = f"Equal split ({bullish_count}-{bearish_count})"
    
    # Calculate confidence (normalized weighted score)
    confidence = abs(weighted_score) / total_weight if total_weight > 0 else 0.0
    confidence = min(1.0, confidence)
    
    # Generate recommendation
    if verdict.startswith('STRONG'):
        recommendation = f"{verdict.split()[1].capitalize()} bias with strong multi-timeframe confirmation."
    elif verdict in ['BULLISH', 'BEARISH']:
        recommendation = f"{verdict.capitalize()} bias with moderate confirmation. Watch for conflicts."
    else:
        recommendation = "No clear bias. Wait for better alignment or trade breakouts."
    
    return {
        'verdict': verdict,
        'confidence': round(confidence, 2),
        'alignment_pct': round(alignment_pct, 1),
        'bullish_count': bullish_count,
        'bearish_count': bearish_count,
        'total_count': total_count,
        'agreement': agreement,
        'recommendation': recommendation
    }


@router.post("/data")
async def get_multi_timeframe_data(
    symbol: str = Body(...),
    timeframes: List[str] = Body(...),
    limit: int = Body(500)
):
    """
    Fetch candlestick data for multiple timeframes in parallel
    
    Example:
        POST /api/multi-timeframe/data
        {
            "symbol": "RELIANCE.NS",
            "timeframes": ["1D", "4H", "1H", "15m"],
            "limit": 500
        }
    
    Returns:
        {
            "success": true,
            "symbol": "RELIANCE.NS",
            "data": {
                "1D": [...candles...],
                "4H": [...candles...],
                "1H": [...candles...],
                "15m": [...candles...]
            },
            "metadata": {...}
        }
    """
    try:
        logger.info(f"📊 Fetching multi-timeframe data for {symbol}: {timeframes}")
        
        # Validate timeframes
        invalid_tfs = [tf for tf in timeframes if tf not in TIMEFRAME_CONFIG]
        if invalid_tfs:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframes: {invalid_tfs}. Valid: {list(TIMEFRAME_CONFIG.keys())}"
            )
        
        # Fetch all timeframes in parallel
        tasks = [fetch_timeframe_data(symbol, tf, limit) for tf in timeframes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build response
        data = {}
        metadata = {}
        
        for i, tf in enumerate(timeframes):
            result = results[i]
            if isinstance(result, Exception):
                logger.error(f"Error fetching {tf}: {result}")
                data[tf] = []
                metadata[tf] = {'error': str(result)}
            else:
                data[tf] = result
                if result:
                    metadata[tf] = {
                        'count': len(result),
                        'start': result[0]['time'] if result else None,
                        'end': result[-1]['time'] if result else None,
                        'interval': TIMEFRAME_CONFIG[tf]['interval'],
                        'label': TIMEFRAME_CONFIG[tf]['label']
                    }
                else:
                    metadata[tf] = {'count': 0, 'error': 'No data available'}
        
        return {
            'success': True,
            'symbol': symbol,
            'data': data,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-timeframe data fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_multi_timeframe(
    symbol: str = Body(...),
    timeframes: List[str] = Body(...),
    analysis_types: List[str] = Body(['structure', 'sr', 'sd'])
):
    """
    Run comprehensive analysis on multiple timeframes
    
    Example:
        POST /api/multi-timeframe/analyze
        {
            "symbol": "RELIANCE.NS",
            "timeframes": ["1D", "4H", "1H", "15m"],
            "analysis_types": ["structure", "sr", "sd"]
        }
    
    Returns complete analysis for each timeframe
    """
    try:
        logger.info(f"🔍 Analyzing {symbol} across {len(timeframes)} timeframes")
        
        # First, fetch all candle data
        data_response = await get_multi_timeframe_data(symbol, timeframes, 500)
        
        if not data_response['success']:
            raise HTTPException(status_code=500, detail="Failed to fetch timeframe data")
        
        candle_data = data_response['data']
        
        # Analyze each timeframe
        analyses = {}
        
        for tf in timeframes:
            if tf not in candle_data or not candle_data[tf]:
                analyses[tf] = {'error': 'No data available'}
                continue
            
            tf_analysis = {}
            candles = candle_data[tf]
            
            # Market Structure
            if 'structure' in analysis_types:
                try:
                    structure_data = await analyze_timeframe_structure(symbol, tf, candles)
                    tf_analysis['structure'] = structure_data
                except Exception as e:
                    logger.error(f"Error analyzing structure for {tf}: {e}")
                    tf_analysis['structure'] = {'error': str(e)}
            
            # Support & Resistance
            if 'sr' in analysis_types:
                try:
                    from api.routes.support_resistance import analyze_support_resistance
                    sr_data = await analyze_support_resistance({'symbol': symbol, 'data': candles})
                    tf_analysis['sr'] = sr_data
                except Exception as e:
                    logger.error(f"Error analyzing S&R for {tf}: {e}")
                    tf_analysis['sr'] = {'error': str(e)}
            
            # Supply & Demand
            if 'sd' in analysis_types:
                try:
                    from api.routes.supply_demand import analyze_supply_demand
                    sd_data = await analyze_supply_demand({'symbol': symbol, 'data': candles})
                    tf_analysis['sd'] = sd_data
                except Exception as e:
                    logger.error(f"Error analyzing S&D for {tf}: {e}")
                    tf_analysis['sd'] = {'error': str(e)}
            
            # Trendlines
            if 'trendlines' in analysis_types:
                try:
                    from api.routes.trendlines import detect_trendlines
                    tl_data = await detect_trendlines({'symbol': symbol, 'data': candles})
                    tf_analysis['trendlines'] = tl_data
                except Exception as e:
                    logger.error(f"Error analyzing trendlines for {tf}: {e}")
                    tf_analysis['trendlines'] = {'error': str(e)}
            
            # Swing Points
            if 'swings' in analysis_types:
                try:
                    from api.routes.swing_points import detect_swing_points
                    swing_data = await detect_swing_points({'symbol': symbol, 'data': candles})
                    tf_analysis['swings'] = swing_data
                except Exception as e:
                    logger.error(f"Error analyzing swings for {tf}: {e}")
                    tf_analysis['swings'] = {'error': str(e)}
            
            analyses[tf] = tf_analysis
        
        return {
            'success': True,
            'symbol': symbol,
            'analyses': analyses,
            'timestamp': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-timeframe analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alignment")
async def get_timeframe_alignment(
    symbol: str = Body(...),
    timeframes: List[str] = Body(...)
):
    """
    Calculate timeframe alignment and trend agreement
    
    Example:
        POST /api/multi-timeframe/alignment
        {
            "symbol": "RELIANCE.NS",
            "timeframes": ["1D", "4H", "1H", "15m"]
        }
    
    Returns alignment analysis with confidence scores
    """
    try:
        logger.info(f"🎯 Calculating alignment for {symbol}: {timeframes}")
        
        # Fetch data for all timeframes
        data_response = await get_multi_timeframe_data(symbol, timeframes, 300)
        
        if not data_response['success']:
            raise HTTPException(status_code=500, detail="Failed to fetch timeframe data")
        
        candle_data = data_response['data']
        
        # Analyze structure for each timeframe
        analyses = {}
        
        for tf in timeframes:
            if tf not in candle_data or not candle_data[tf]:
                continue
            
            analysis = await analyze_timeframe_structure(symbol, tf, candle_data[tf])
            analyses[tf] = analysis
        
        # Calculate overall alignment
        overall = calculate_timeframe_alignment(analyses)
        
        # Format timeframe details
        timeframe_details = {}
        for tf, analysis in analyses.items():
            timeframe_details[tf] = {
                'trend': analysis['trend'],
                'confidence': analysis['confidence'],
                'structure': f"{analysis['trend'].capitalize()} structure detected",
                'last_bos': analysis['last_bos'] or 'None'
            }
        
        return {
            'success': True,
            'symbol': symbol,
            'alignment': {
                'timeframes': timeframe_details,
                'overall': overall
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating alignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeframes")
async def get_available_timeframes():
    """Get list of all available timeframes with details"""
    return {
        'success': True,
        'timeframes': [
            {
                'value': tf,
                'label': config['label'],
                'interval': config['interval'],
                'period': config['period'],
                'weight': config['weight'],
                'category': 'intraday' if tf in ['1m', '5m', '15m', '30m', '1H', '4H'] else 'daily'
            }
            for tf, config in TIMEFRAME_CONFIG.items()
        ]
    }

