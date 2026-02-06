"""
Real-time Options Chain Service
Real-time options data with delta updates and pagination
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class RealtimeOptionsChain:
    """Real-time options chain with delta updates"""
    
    def __init__(self):
        self.options_chains: Dict[str, Dict] = {}  # symbol -> options chain data
        self.last_states: Dict[str, Dict] = {}  # symbol -> last full state
        self.min_update_interval = 1.0  # 1 second minimum between updates
        self.last_update_time: Dict[str, float] = {}
        self.page_size = 20  # Default strikes per page
        
    async def get_options_chain(
        self,
        symbol: str,
        expiry_date: Optional[str] = None,
        page: int = 1,
        page_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get options chain for symbol with pagination"""
        try:
            page_size = page_size or self.page_size
            
            # This would integrate with your options data provider
            # For now, return mock data structure
            if symbol not in self.options_chains:
                self.options_chains[symbol] = {
                    "symbol": symbol,
                    "expiry_dates": [],
                    "strikes": [],
                    "calls": {},
                    "puts": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            chain = self.options_chains[symbol]
            
            # Paginate strikes
            all_strikes = sorted(chain.get("strikes", []))
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_strikes = all_strikes[start_idx:end_idx]
            
            # Get data for paginated strikes
            paginated_calls = {
                strike: chain["calls"].get(strike, {})
                for strike in paginated_strikes
            }
            paginated_puts = {
                strike: chain["puts"].get(strike, {})
                for strike in paginated_strikes
            }
            
            return {
                "symbol": symbol,
                "expiry_dates": chain.get("expiry_dates", []),
                "strikes": paginated_strikes,
                "calls": paginated_calls,
                "puts": paginated_puts,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_strikes": len(all_strikes),
                    "total_pages": (len(all_strikes) + page_size - 1) // page_size
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting options chain for {symbol}: {e}")
            return {"error": str(e)}
    
    async def get_delta_update(self, symbol: str, last_state: Optional[Dict] = None) -> Dict[str, Any]:
        """Get delta update (only changed strikes) for options chain"""
        try:
            current_chain = await self.get_options_chain(symbol, page=1, page_size=1000)
            
            if last_state is None:
                self.last_states[symbol] = current_chain
                return current_chain
            
            # Calculate delta
            delta = {
                "symbol": symbol,
                "changed_strikes": [],
                "removed_strikes": [],
                "new_strikes": [],
                "timestamp": datetime.now().isoformat()
            }
            
            last_strikes = set(last_state.get("strikes", []))
            current_strikes = set(current_chain.get("strikes", []))
            
            # New strikes
            delta["new_strikes"] = list(current_strikes - last_strikes)
            
            # Removed strikes
            delta["removed_strikes"] = list(last_strikes - current_strikes)
            
            # Changed strikes (check if OI, IV, or price changed)
            common_strikes = last_strikes & current_strikes
            for strike in common_strikes:
                last_call = last_state.get("calls", {}).get(strike, {})
                current_call = current_chain.get("calls", {}).get(strike, {})
                last_put = last_state.get("puts", {}).get(strike, {})
                current_put = current_chain.get("puts", {}).get(strike, {})
                
                if (last_call != current_call or last_put != current_put):
                    delta["changed_strikes"].append({
                        "strike": strike,
                        "call": current_call,
                        "put": current_put
                    })
            
            # Update last state
            self.last_states[symbol] = current_chain
            
            return delta
            
        except Exception as e:
            logger.error(f"Error getting delta update for {symbol}: {e}")
            return {"error": str(e)}
    
    def should_update(self, symbol: str) -> bool:
        """Check if enough time has passed for update"""
        current_time = time.time()
        last_update = self.last_update_time.get(symbol, 0)
        
        if current_time - last_update >= self.min_update_interval:
            self.last_update_time[symbol] = current_time
            return True
        return False

# Create singleton instance
realtime_options_chain = RealtimeOptionsChain()

