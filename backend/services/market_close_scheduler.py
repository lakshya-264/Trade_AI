"""
Market Close Scheduler - Automated Daily Analysis
"""

import asyncio
import logging
from datetime import time, date, datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

from services.daily_comparison_service import daily_comparison_service
from core.database import SessionLocal

logger = logging.getLogger(__name__)

class MarketCloseScheduler:
    """Scheduler for automated daily market close analysis"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.timezone = timezone('Asia/Kolkata')
        self.market_close_time = time(15, 45)  # 3:45 PM IST
        
    async def market_close_analysis(self):
        """Run comprehensive analysis after market close"""
        try:
            today = date.today()
            logger.info(f"🚀 Starting market close analysis for {today}")
            
            # Check if today is a trading day (weekday)
            if today.weekday() >= 5:  # Saturday (5) or Sunday (6)
                logger.info("Today is weekend - skipping market analysis")
                return
            
            # Create database session
            db = SessionLocal()
            
            try:
                # Generate daily comparison for all users
                results = await daily_comparison_service.generate_daily_comparison(today, db)
                
                # Log summary
                market_summary = results.get('market_summary', {})
                user_comparisons = results.get('user_comparisons', [])
                
                logger.info("📊 MARKET CLOSE ANALYSIS SUMMARY:")
                logger.info(f"  Date: {today}")
                logger.info(f"  Market Return: {market_summary.get('market_return', 0):.2f}%")
                logger.info(f"  Users Analyzed: {market_summary.get('total_users_analyzed', 0)}")
                logger.info(f"  Avg User Return: {market_summary.get('avg_user_return', 0):.2f}%")
                logger.info(f"  Users Beating Market: {market_summary.get('percent_beating_market', 0):.1f}%")
                
                # Rank users by performance
                ranked_users = sorted(
                    user_comparisons, 
                    key=lambda x: x.get('score', 0), 
                    reverse=True
                )
                
                if ranked_users:
                    logger.info("🏆 TOP PERFORMERS:")
                    for i, user in enumerate(ranked_users[:5], 1):
                        user_return = user.get('portfolio_return', 0)
                        user_grade = user.get('grade', 'N/A')
                        logger.info(f"  {i}. User {user.get('user_id', 'Unknown')}: {user_return:.2f}% ({user_grade})")
                
                # Strategy performance summary
                strategy_perf = results.get('strategy_performance', {})
                if strategy_perf:
                    logger.info("📈 STRATEGY PERFORMANCE:")
                    sorted_strategies = sorted(
                        strategy_perf.items(),
                        key=lambda x: x[1].get('total_return', 0),
                        reverse=True
                    )
                    
                    for strategy, metrics in sorted_strategies[:5]:
                        total_return = metrics.get('total_return', 0)
                        win_rate = metrics.get('win_rate', 0)
                        logger.info(f"  {strategy}: {total_return:.2f}% (Win Rate: {win_rate:.1%})")
                
                # Generate and send notifications (if implemented)
                await self._send_daily_notifications(results, db)
                
                logger.info("✅ Market close analysis completed successfully")
                
            except Exception as e:
                logger.error(f"Error in market close analysis: {e}")
                raise
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Critical error in market close analysis: {e}")
    
    async def _send_daily_notifications(
        self, 
        results: Dict[str, Any], 
        db
    ):
        """Send daily performance notifications to users"""
        try:
            user_comparisons = results.get('user_comparisons', [])
            
            for user_comparison in user_comparisons:
                user_id = user_comparison.get('user_id')
                user_return = user_comparison.get('portfolio_return', 0)
                user_grade = user_comparison.get('grade', 'N/A')
                insights = user_comparison.get('insights', {})
                
                # Create notification message
                message = self._create_notification_message(
                    user_return, user_grade, insights
                )
                
                # In a real implementation, send email/push notification
                logger.info(f"📧 Notification for User {user_id}: {message}")
                
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    def _create_notification_message(
        self, 
        user_return: float, 
        user_grade: str, 
        insights: Dict[str, Any]
    ) -> str:
        """Create personalized notification message"""
        try:
            emoji = "🟢" if user_return > 0 else "🔴" if user_return < -1 else "🟡"
            
            message = f"{emoji} Daily Performance: {user_return:.2f}% (Grade: {user_grade})\n"
            
            if user_return > 1.0:
                message += "🎉 Excellent performance today! Keep it up!"
            elif user_return > 0:
                message += "👍 Good positive returns today!"
            elif user_return > -1:
                message += "📊 Small loss today, tomorrow is another day!"
            else:
                message += "⚠️ Review your strategy for better results."
            
            # Add top recommendation
            recommendations = insights.get('recommendations', [])
            if recommendations:
                message += f"\n💡 Tip: {recommendations[0]}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating notification message: {e}")
            return "Daily performance report available"
    
    def start_scheduler(self):
        """Start the automated scheduler"""
        try:
            logger.info("🚀 Starting Market Close Scheduler")
            
            # Schedule daily analysis at 3:45 PM IST
            self.scheduler.add_job(
                self.market_close_analysis,
                'cron',
                hour=15,  # 3 PM IST
                minute=45,  # 45 minutes
                second=0,
                timezone=self.timezone,
                id='market_close_analysis',
                name='Daily Market Close Analysis',
                replace_existing=True,
                misfire_grace_time=300  # 5 minutes grace period
            )
            
            # Schedule backup run at 4:00 PM IST (in case 3:45 PM fails)
            self.scheduler.add_job(
                self.market_close_analysis,
                'cron',
                hour=16,  # 4 PM IST
                minute=0,  # 0 minutes
                second=0,
                timezone=self.timezone,
                id='market_close_analysis_backup',
                name='Daily Market Close Analysis (Backup)',
                replace_existing=True,
                misfire_grace_time=300
            )
            
            self.scheduler.start()
            logger.info("✅ Market Close Scheduler started successfully")
            logger.info("📅 Scheduled runs: 3:45 PM IST (Primary) & 4:00 PM IST (Backup)")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("🛑 Market Close Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def get_next_run_time(self) -> str:
        """Get the next scheduled run time"""
        try:
            job = self.scheduler.get_job('market_close_analysis')
            if job:
                next_run = job.next_run_time
                if next_run:
                    return next_run.astimezone(self.timezone).strftime('%Y-%m-%d %H:%M:%S %Z')
            return "No scheduled run found"
        except Exception as e:
            logger.error(f"Error getting next run time: {e}")
            return "Error getting next run time"
    
    async def run_manual_analysis(self, analysis_date: date = None):
        """Run analysis manually for testing or specific date"""
        try:
            target_date = analysis_date or date.today()
            logger.info(f"🔧 Running manual analysis for {target_date}")
            
            db = SessionLocal()
            try:
                results = await daily_comparison_service.generate_daily_comparison(target_date, db)
                logger.info("✅ Manual analysis completed successfully")
                return results
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in manual analysis: {e}")
            raise

# Create global scheduler instance
market_close_scheduler = MarketCloseScheduler()
