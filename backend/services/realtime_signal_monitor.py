"""
Realtime signal monitor
"""
from core.websocket_manager import WebSocketManager
from core.redis_client import redis_client

class RealtimeSignalMonitor:
    def __init__(self):
        self.websocket_manager = WebSocketManager()
    
    async def start_monitoring(self):
        """Start monitoring signals"""
        pass


# Create instance
ealtime_monitor = RealtimeSignalMonitor()


# Create instance
realtime_monitor = RealtimeSignalMonitor()
