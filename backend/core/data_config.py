"""
Configuration for Data Sources
Controls whether to use real NSE data or mock data
"""

import os
from typing import Dict, Any

class DataSourceConfig:
    def __init__(self):
        # Environment variables to control data sources
        self.use_real_nse_data = os.getenv("USE_REAL_NSE_DATA", "false").lower() == "true"
        self.nse_api_enabled = os.getenv("NSE_API_ENABLED", "true").lower() == "true"
        self.fallback_to_mock = os.getenv("FALLBACK_TO_MOCK", "true").lower() == "true"
        
        # Rate limiting settings
        self.nse_rate_limit_per_minute = int(os.getenv("NSE_RATE_LIMIT", "60"))
        self.cache_ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", "30"))
        
        # Debug settings
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.log_data_source = os.getenv("LOG_DATA_SOURCE", "true").lower() == "true"
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            "use_real_nse_data": self.use_real_nse_data,
            "nse_api_enabled": self.nse_api_enabled,
            "fallback_to_mock": self.fallback_to_mock,
            "nse_rate_limit_per_minute": self.nse_rate_limit_per_minute,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "debug_mode": self.debug_mode,
            "log_data_source": self.log_data_source
        }
    
    def should_use_real_data(self) -> bool:
        """Check if real NSE data should be used"""
        return self.use_real_nse_data and self.nse_api_enabled
    
    def should_fallback_to_mock(self) -> bool:
        """Check if should fallback to mock data"""
        return self.fallback_to_mock

# Global configuration instance
data_config = DataSourceConfig()
