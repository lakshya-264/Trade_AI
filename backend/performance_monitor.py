#!/usr/bin/env python3
"""
Performance Monitor for Trading API
"""

import asyncio
import aiohttp
import time
import psutil
import json
from datetime import datetime

class PerformanceMonitor:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_api_health(self):
        """Check API health and response time"""
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    response_time = time.time() - start_time
                    return {
                        "status": "healthy",
                        "response_time": response_time,
                        "timestamp": datetime.now().isoformat(),
                        "services": data.get("services", {})
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "response_time": time.time() - start_time,
                        "timestamp": datetime.now().isoformat(),
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "response_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def check_nifty50_api(self):
        """Check Nifty50 API performance"""
        try:
            start_time = time.time()
            async with self.session.get(
                f"{self.base_url}/api/public/nifty50-signals?symbol=TCS&use_cache=false",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_time = time.time() - start_time
                    return {
                        "status": "healthy",
                        "response_time": response_time,
                        "timestamp": datetime.now().isoformat(),
                        "data_count": data.get("count", 0),
                        "cached": data.get("cached", False)
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "response_time": time.time() - start_time,
                        "timestamp": datetime.now().isoformat(),
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                "status": "error",
                "response_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_system_stats(self):
        """Get system performance statistics"""
        process = psutil.Process()
        return {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "threads": process.num_threads(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def run_monitoring(self, duration_minutes=5):
        """Run continuous monitoring"""
        print(f"🔍 Starting performance monitoring for {duration_minutes} minutes...")
        print("=" * 60)
        
        start_time = time.time()
        check_interval = 30  # Check every 30 seconds
        
        while time.time() - start_time < duration_minutes * 60:
            # Check API health
            health = await self.check_api_health()
            print(f"🏥 Health: {health['status']} | Response: {health['response_time']:.2f}s")
            
            # Check Nifty50 API
            nifty50 = await self.check_nifty50_api()
            print(f"📈 Nifty50 API: {nifty50['status']} | Response: {nifty50['response_time']:.2f}s | Cached: {nifty50.get('cached', False)}")
            
            # Get system stats
            system = self.get_system_stats()
            print(f"💾 Memory: {system['memory_mb']:.1f}MB ({system['memory_percent']:.1f}%) | CPU: {system['cpu_percent']:.1f}%")
            
            print("-" * 60)
            
            # Alert on performance issues
            if health['response_time'] > 2.0:
                print(f"⚠️  SLOW HEALTH CHECK: {health['response_time']:.2f}s")
            
            if nifty50['response_time'] > 5.0:
                print(f"⚠️  SLOW NIFTY50 API: {nifty50['response_time']:.2f}s")
            
            if system['memory_mb'] > 500:
                print(f"⚠️  HIGH MEMORY USAGE: {system['memory_mb']:.1f}MB")
            
            await asyncio.sleep(check_interval)
        
        print("🏁 Monitoring completed!")

async def main():
    async with PerformanceMonitor() as monitor:
        await monitor.run_monitoring(duration_minutes=5)

if __name__ == "__main__":
    asyncio.run(main())
