import sys
sys.path.append('.')

# Clear all caches
from api.routes.nifty50_public import _nifty50_cache
from core.data_service import data_service

print('Clearing all caches...')

# Clear Nifty50 cache
print(f"Nifty50 cache size before clearing: {len(_nifty50_cache)}")
_nifty50_cache.clear()
print(f"Nifty50 cache size after clearing: {len(_nifty50_cache)}")

# Clear data service cache
if hasattr(data_service, 'cache'):
    print(f"Data service cache size before clearing: {len(data_service.cache)}")
    data_service.cache.clear()
    print(f"Data service cache size after clearing: {len(data_service.cache)}")
else:
    print("Data service cache not found")

print('All caches cleared successfully!')
