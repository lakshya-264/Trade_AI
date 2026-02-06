"""
Sentiment Analysis Scheduling and Automation System
Handles automated data collection with proper scheduling and rate limiting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import json
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
from pathlib import Path
from .enhanced_sentiment_analysis import EnhancedSentimentAnalysisService
from .reddit_sentiment import RedditSentimentCollector
from .news_sentiment import NewsSentimentCollector
from .economic_indicators import EconomicIndicatorsCollector
from .forum_sentiment import ForumSentimentCollector

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ScheduledTask:
    """Represents a scheduled task"""
    id: str
    name: str
    function: Callable
    schedule: str  # Cron-like expression or interval in minutes
    priority: TaskPriority
    status: TaskStatus
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    enabled: bool = True
    metadata: Dict[str, Any] = None

class SentimentScheduler:
    """Advanced scheduler for sentiment analysis tasks"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize sentiment scheduler
        
        Args:
            config: Configuration dictionary containing API keys and settings
        """
        self.config = config or {}
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.scheduler_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # Initialize collectors
        self.sentiment_service = None
        self.reddit_collector = None
        self.news_collector = None
        self.economic_collector = None
        self.forum_collector = None
        
        # Storage for task results
        self.results_cache = {}
        self.cache_file = Path("sentiment_cache.json")
        
        # Rate limiting
        self.rate_limits = {
            'reddit': {'calls': 60, 'period': 60},     # 60 calls per minute
            'news': {'calls': 1000, 'period': 3600},    # 1000 calls per hour
            'economic': {'calls': 100, 'period': 3600},  # 100 calls per hour
            'forum': {'calls': 200, 'period': 3600}     # 200 calls per hour
        }
        
        self.api_call_counts = {}
        
        logger.info("Sentiment scheduler initialized")
    
    async def initialize(self) -> bool:
        """Initialize all collectors and services"""
        try:
            # Initialize enhanced sentiment service
            self.sentiment_service = EnhancedSentimentAnalysisService(self.config)
            
            # Initialize individual collectors
            api_config = self.config.get('api_keys', {})
            
            # Reddit collector
            if api_config.get('reddit'):
                self.reddit_collector = RedditSentimentCollector(api_config['reddit'])
                await self.reddit_collector.initialize()
            
            # News collector
            if api_config.get('news'):
                self.news_collector = NewsSentimentCollector(api_config['news'])
                await self.news_collector.initialize()
            
            # Economic collector
            self.economic_collector = EconomicIndicatorsCollector(api_config.get('economic', {}))
            await self.economic_collector.initialize()
            
            # Forum collector
            self.forum_collector = ForumSentimentCollector(api_config.get('forum', {}))
            await self.forum_collector.initialize()
            
            # Load cached results
            await self._load_cache()
            
            # Setup default tasks
            await self._setup_default_tasks()
            
            logger.info("Scheduler initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"Scheduler initialization failed: {e}")
            return False
    
    async def start_scheduler(self):
        """Start the background scheduler"""
        try:
            if self.scheduler_running:
                logger.warning("Scheduler is already running")
                return
            
            self.scheduler_running = True
            self.scheduler_task = asyncio.create_task(self._scheduler_loop())
            logger.info("Scheduler started")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
    
    async def stop_scheduler(self):
        """Stop the background scheduler"""
        try:
            self.scheduler_running = False
            
            # Cancel scheduler task
            if self.scheduler_task:
                self.scheduler_task.cancel()
                try:
                    await self.scheduler_task
                except asyncio.CancelledError:
                    pass
            
            # Cancel all running tasks
            for task_id, task in self.running_tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self.running_tasks.clear()
            
            # Save cache
            await self._save_cache()
            
            logger.info("Scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def add_task(self, task: ScheduledTask):
        """Add a new scheduled task"""
        try:
            # Calculate next run time
            task.next_run = self._calculate_next_run(task.schedule)
            task.status = TaskStatus.PENDING
            
            self.tasks[task.id] = task
            logger.info(f"Task added: {task.name} (ID: {task.id})")
            
        except Exception as e:
            logger.error(f"Error adding task: {e}")
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        try:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                
                # Cancel if running
                if task_id in self.running_tasks:
                    self.running_tasks[task_id].cancel()
                    del self.running_tasks[task_id]
                
                del self.tasks[task_id]
                logger.info(f"Task removed: {task.name} (ID: {task_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing task: {e}")
            return False
    
    def enable_task(self, task_id: str) -> bool:
        """Enable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """Disable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            return True
        return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return {
                'id': task.id,
                'name': task.name,
                'status': task.status.value,
                'enabled': task.enabled,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'next_run': task.next_run.isoformat() if task.next_run else None,
                'run_count': task.run_count,
                'error_count': task.error_count,
                'last_error': task.last_error
            }
        return None
    
    def get_all_tasks_status(self) -> List[Dict[str, Any]]:
        """Get status of all tasks"""
        return [self.get_task_status(task_id) for task_id in self.tasks.keys()]
    
    async def run_task_now(self, task_id: str) -> bool:
        """Run a task immediately"""
        try:
            if task_id not in self.tasks:
                logger.error(f"Task not found: {task_id}")
                return False
            
            task = self.tasks[task_id]
            
            if task.status == TaskStatus.RUNNING:
                logger.warning(f"Task already running: {task_id}")
                return False
            
            # Execute task
            await self._execute_task(task)
            
            return True
            
        except Exception as e:
            logger.error(f"Error running task {task_id}: {e}")
            return False
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Scheduler loop started")
        
        while self.scheduler_running:
            try:
                current_time = datetime.utcnow()
                
                # Check for tasks that need to run
                for task_id, task in self.tasks.items():
                    if (task.enabled and 
                        task.status != TaskStatus.RUNNING and
                        task.next_run and 
                        task.next_run <= current_time):
                        
                        # Check rate limits
                        if await self._check_rate_limits(task):
                            # Execute task
                            asyncio.create_task(self._execute_task(task))
                        else:
                            logger.warning(f"Rate limit exceeded for task: {task.name}")
                
                # Sleep for 1 minute
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
        
        logger.info("Scheduler loop stopped")
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        try:
            task.status = TaskStatus.RUNNING
            task.last_run = datetime.utcnow()
            task.run_count += 1
            
            logger.info(f"Executing task: {task.name}")
            
            # Execute the task function
            if asyncio.iscoroutinefunction(task.function):
                result = await task.function()
            else:
                result = task.function()
            
            # Store result
            self.results_cache[task.id] = {
                'timestamp': task.last_run.isoformat(),
                'result': result,
                'success': True
            }
            
            # Update task
            task.status = TaskStatus.COMPLETED
            task.last_error = None
            
            # Calculate next run time
            task.next_run = self._calculate_next_run(task.schedule)
            
            logger.info(f"Task completed: {task.name}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_count += 1
            task.last_error = str(e)
            
            # Store error result
            self.results_cache[task.id] = {
                'timestamp': task.last_run.isoformat() if task.last_run else datetime.utcnow().isoformat(),
                'result': None,
                'success': False,
                'error': str(e)
            }
            
            # Calculate next run time (with backoff for errors)
            if task.error_count < 3:
                task.next_run = datetime.utcnow() + timedelta(minutes=5)
            else:
                task.next_run = datetime.utcnow() + timedelta(hours=1)
            
            logger.error(f"Task failed: {task.name} - {e}")
        
        finally:
            # Clean up running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
    
    def _calculate_next_run(self, schedule: str) -> datetime:
        """Calculate next run time based on schedule"""
        try:
            if schedule.isdigit():
                # Simple interval in minutes
                interval_minutes = int(schedule)
                return datetime.utcnow() + timedelta(minutes=interval_minutes)
            
            # Handle cron-like expressions (simplified)
            elif schedule.startswith('*/'):
                # Every N minutes/hours
                parts = schedule.split()
                if len(parts) == 2:
                    if parts[1] == 'minute':
                        interval = int(parts[0][2:])
                        return datetime.utcnow() + timedelta(minutes=interval)
                    elif parts[1] == 'hour':
                        interval = int(parts[0][2:])
                        return datetime.utcnow() + timedelta(hours=interval)
            
            # Default: 1 hour
            return datetime.utcnow() + timedelta(hours=1)
            
        except Exception:
            # Default fallback
            return datetime.utcnow() + timedelta(hours=1)
    
    async def _check_rate_limits(self, task: ScheduledTask) -> bool:
        """Check if API rate limits allow task execution"""
        try:
            # Determine which API the task uses
            api_type = task.metadata.get('api_type', 'unknown')
            
            if api_type not in self.rate_limits:
                return True  # No rate limiting for unknown APIs
            
            limit = self.rate_limits[api_type]
            current_time = datetime.utcnow()
            
            # Initialize call count if needed
            if api_type not in self.api_call_counts:
                self.api_call_counts[api_type] = []
            
            # Clean old calls outside the period
            cutoff_time = current_time - timedelta(seconds=limit['period'])
            self.api_call_counts[api_type] = [
                call_time for call_time in self.api_call_counts[api_type]
                if call_time > cutoff_time
            ]
            
            # Check if we're under the limit
            if len(self.api_call_counts[api_type]) < limit['calls']:
                # Record this call
                self.api_call_counts[api_type].append(current_time)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rate limits: {e}")
            return True  # Allow execution on error
    
    async def _setup_default_tasks(self):
        """Setup default scheduled tasks"""
        try:
            # Reddit sentiment collection (every hour)
            if self.reddit_collector:
                self.add_task(ScheduledTask(
                    id='reddit_sentiment',
                    name='Reddit Sentiment Collection',
                    function=self._collect_reddit_sentiment,
                    schedule='60',  # Every hour
                    priority=TaskPriority.MEDIUM,
                    status=TaskStatus.PENDING,
                    metadata={'api_type': 'reddit', 'subreddits': ['r/IndianStockMarket', 'r/investing']}
                ))
            
            # News sentiment collection (every 30 minutes)
            if self.news_collector:
                self.add_task(ScheduledTask(
                    id='news_sentiment',
                    name='News Sentiment Collection',
                    function=self._collect_news_sentiment,
                    schedule='30',  # Every 30 minutes
                    priority=TaskPriority.HIGH,
                    status=TaskStatus.PENDING,
                    metadata={'api_type': 'news', 'symbols': ['NIFTY', 'SENSEX', 'RELIANCE']}
                ))
            
            # Economic indicators collection (every 4 hours)
            if self.economic_collector:
                self.add_task(ScheduledTask(
                    id='economic_indicators',
                    name='Economic Indicators Collection',
                    function=self._collect_economic_indicators,
                    schedule='240',  # Every 4 hours
                    priority=TaskPriority.LOW,
                    status=TaskStatus.PENDING,
                    metadata={'api_type': 'economic', 'indicators': ['RBI', 'inflation', 'GDP']}
                ))
            
            # Forum sentiment collection (every 2 hours)
            if self.forum_collector:
                self.add_task(ScheduledTask(
                    id='forum_sentiment',
                    name='Forum Sentiment Collection',
                    function=self._collect_forum_sentiment,
                    schedule='120',  # Every 2 hours
                    priority=TaskPriority.MEDIUM,
                    status=TaskStatus.PENDING,
                    metadata={'api_type': 'forum', 'sources': ['moneycontrol', 'valuepickr']}
                ))
            
            # Comprehensive analysis (every hour)
            self.add_task(ScheduledTask(
                id='comprehensive_analysis',
                name='Comprehensive Sentiment Analysis',
                function=self._run_comprehensive_analysis,
                schedule='60',  # Every hour
                priority=TaskPriority.CRITICAL,
                status=TaskStatus.PENDING,
                metadata={'api_type': 'internal'}
            ))
            
            logger.info("Default tasks setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up default tasks: {e}")
    
    # Task execution functions
    async def _collect_reddit_sentiment(self) -> Dict[str, Any]:
        """Collect Reddit sentiment"""
        try:
            subreddits = ['IndianStockMarket', 'investing', 'stocks']
            data = await self.reddit_collector.collect_posts(subreddits, limit=25)
            
            return {
                'source': 'reddit',
                'count': len(data),
                'subreddits': subreddits,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Reddit collection error: {e}")
            raise
    
    async def _collect_news_sentiment(self) -> Dict[str, Any]:
        """Collect news sentiment"""
        try:
            symbols = ['RELIANCE.BSE', 'TCS.BSE', 'INFY.BSE']
            data = await self.news_collector.collect_all_news(symbols, hours_back=6)
            
            return {
                'source': 'news',
                'count': len(data),
                'symbols': symbols,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"News collection error: {e}")
            raise
    
    async def _collect_economic_indicators(self) -> Dict[str, Any]:
        """Collect economic indicators"""
        try:
            data = await self.economic_collector.collect_all_indicators()
            
            return {
                'source': 'economic',
                'indicators': list(data.keys()),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Economic collection error: {e}")
            raise
    
    async def _collect_forum_sentiment(self) -> Dict[str, Any]:
        """Collect forum sentiment"""
        try:
            symbols = ['NIFTY', 'RELIANCE', 'TCS', 'HDFC']
            data = await self.forum_collector.collect_all_forum_posts(symbols, max_posts_per_source=25)
            
            return {
                'source': 'forum',
                'count': len(data),
                'symbols': symbols,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Forum collection error: {e}")
            raise
    
    async def _run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive sentiment analysis"""
        try:
            if not self.sentiment_service:
                raise Exception("Sentiment service not initialized")
            
            symbols = ['NIFTY', 'SENSEX']
            result = await self.sentiment_service.run_comprehensive_analysis(symbols)
            
            return {
                'source': 'comprehensive',
                'symbols': symbols,
                'analysis_key': result.get('summary', ''),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis error: {e}")
            raise
    
    async def _load_cache(self):
        """Load cached results from file"""
        try:
            if self.cache_file.exists():
                async with aiofiles.open(self.cache_file, 'r') as f:
                    content = await f.read()
                    self.results_cache = json.loads(content)
                logger.info(f"Loaded {len(self.results_cache)} cached results")
        except Exception as e:
            logger.warning(f"Error loading cache: {e}")
    
    async def _save_cache(self):
        """Save cached results to file"""
        try:
            async with aiofiles.open(self.cache_file, 'w') as f:
                await f.write(json.dumps(self.results_cache, indent=2))
            logger.info(f"Saved {len(self.results_cache)} cached results")
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")
    
    async def get_task_results(self, task_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent results for a task"""
        try:
            if task_id in self.results_cache:
                return [self.results_cache[task_id]]
            return []
        except Exception as e:
            logger.error(f"Error getting task results: {e}")
            return []
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.stop_scheduler()
            
            # Cleanup collectors
            if self.reddit_collector:
                pass  # Reddit client doesn't need explicit cleanup
            if self.news_collector:
                await self.news_collector.cleanup()
            if self.economic_collector:
                await self.economic_collector.cleanup()
            if self.forum_collector:
                await self.forum_collector.cleanup()
            
            logger.info("Scheduler cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Factory function
async def create_sentiment_scheduler(config: Dict[str, Any] = None) -> SentimentScheduler:
    """Create and initialize sentiment scheduler"""
    scheduler = SentimentScheduler(config)
    await scheduler.initialize()
    return scheduler
