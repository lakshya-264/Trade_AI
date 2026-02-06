"""
Redis client
"""
import asyncio

class RedisClient:
    def __init__(self):
        self.connected = False
    
    async def connect(self):
        """Connect to Redis"""
        self.connected = True
    
    async def ping(self) -> bool:
        """Ping Redis"""
        return self.connected
    
    async def get(self, key: str):
        """Get value from Redis"""
        return None
    
    async def set(self, key: str, value: str, expire: int = None):
        """Set value in Redis"""
        pass

redis_client = RedisClient()
