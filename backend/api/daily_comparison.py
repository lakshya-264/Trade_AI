"""
Daily Comparison API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

from core.database import get_db
from services.daily_comparison_service import daily_comparison_service
from services.market_close_scheduler import market_close_scheduler
from core.auth_dependencies import get_current_active_user
from core.database_unified import User

router = APIRouter(prefix="/api/v1/daily-comparison", tags=["Daily Comparison"])

@router.get("/summary")
async def get_daily_comparison_summary(
    analysis_date: str = Query(..., description="Date in YYYY-MM-DD format"),
    user_id: int = Query(None, description="User ID (optional, for admin access)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get daily comparison summary for a specific date"""
    try:
        # Parse date
        target_date = datetime.strptime(analysis_date, "%Y-%m-%d").date()
        
        # Check if user is requesting their own data or is admin
        if user_id and user_id != current_user.id:
            # In a real implementation, check if user is admin
            pass
        
        # Generate comparison for the specific date
        results = await daily_comparison_service.generate_daily_comparison(target_date, db)
        
        # Filter results for current user if not admin
        if not user_id or user_id == current_user.id:
            user_comparison = next(
                (uc for uc in results.get('user_comparisons', []) 
                 if uc.get('user_id') == current_user.id), 
                None
            )
            
            return {
                'success': True,
                'data': {
                    'date': results.get('date'),
                    'market_data': results.get('market_data'),
                    'user_comparison': user_comparison,
                    'strategy_performance': results.get('strategy_performance'),
                    'market_summary': results.get('market_summary')
                },
                'message': f'Daily comparison for {analysis_date}'
            }
        else:
            # Return full results for admin
            return {
                'success': True,
                'data': results,
                'message': f'Full daily comparison for {analysis_date}'
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily comparison: {str(e)}")

@router.get("/history")
async def get_daily_comparison_history(
    days: int = Query(30, description="Number of days to analyze"),
    user_id: int = Query(None, description="User ID (optional)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get historical daily comparisons"""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        history = []
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday to Friday
                try:
                    results = await daily_comparison_service.generate_daily_comparison(current_date, db)
                    
                    # Filter for specific user if requested
                    if user_id:
                        user_comparison = next(
                            (uc for uc in results.get('user_comparisons', []) 
                             if uc.get('user_id') == user_id), 
                            None
                        )
                        if user_comparison:
                            history.append({
                                'date': current_date.isoformat(),
                                'user_comparison': user_comparison,
                                'market_summary': results.get('market_summary')
                            })
                    else:
                        # Get current user's comparison
                        user_comparison = next(
                            (uc for uc in results.get('user_comparisons', []) 
                             if uc.get('user_id') == current_user.id), 
                            None
                        )
                        if user_comparison:
                            history.append({
                                'date': current_date.isoformat(),
                                'user_comparison': user_comparison,
                                'market_summary': results.get('market_summary')
                            })
                            
                except Exception as e:
                    logger.error(f"Error getting comparison for {current_date}: {e}")
                    continue
            
            current_date += timedelta(days=1)
        
        return {
            'success': True,
            'data': {
                'history': history,
                'period_days': days,
                'total_analyzed': len(history)
            },
            'message': f'Historical comparison for {days} days'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get historical comparison: {str(e)}")

@router.get("/market-summary")
async def get_market_summary(
    analysis_date: str = Query(None, description="Date in YYYY-MM-DD format (optional)"),
    db: Session = Depends(get_db)
):
    """Get market-wide summary for a specific date"""
    try:
        target_date = analysis_date
        if not target_date:
            target_date = date.today()
        else:
            target_date = datetime.strptime(analysis_date, "%Y-%m-%d").date()
        
        # Generate full comparison to get market summary
        results = await daily_comparison_service.generate_daily_comparison(target_date, db)
        
        return {
            'success': True,
            'data': {
                'date': results.get('date'),
                'market_data': results.get('market_data'),
                'market_summary': results.get('market_summary'),
                'strategy_performance': results.get('strategy_performance')
            },
            'message': f'Market summary for {target_date}'
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market summary: {str(e)}")

@router.get("/leaderboard")
async def get_daily_leaderboard(
    analysis_date: str = Query(None, description="Date in YYYY-MM-DD format (optional)"),
    limit: int = Query(10, description="Number of top performers to return"),
    db: Session = Depends(get_db)
):
    """Get daily performance leaderboard"""
    try:
        target_date = analysis_date
        if not target_date:
            target_date = date.today()
        else:
            target_date = datetime.strptime(analysis_date, "%Y-%m-%d").date()
        
        # Generate full comparison
        results = await daily_comparison_service.generate_daily_comparison(target_date, db)
        
        # Sort users by score and get top performers
        user_comparisons = results.get('user_comparisons', [])
        sorted_users = sorted(
            user_comparisons,
            key=lambda x: (x.get('score', 0), x.get('portfolio_return', 0)),
            reverse=True
        )
        
        leaderboard = sorted_users[:limit]
        
        # Add rank positions
        for rank, user in enumerate(leaderboard, 1):
            user['rank_position'] = rank
        
        return {
            'success': True,
            'data': {
                'date': target_date.isoformat(),
                'leaderboard': leaderboard,
                'market_summary': results.get('market_summary'),
                'total_participants': len(user_comparisons)
            },
            'message': f'Daily leaderboard for {target_date}'
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")

@router.post("/manual-analysis")
async def trigger_manual_analysis(
    analysis_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Trigger manual analysis for a specific date"""
    try:
        target_date = analysis_data.get('date')
        if target_date:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        # Check if user has permission (admin or self-analysis)
        user_id = analysis_data.get('user_id')
        if user_id and user_id != current_user.id:
            # In a real implementation, check if user is admin
            pass
        
        # Run manual analysis
        results = await market_close_scheduler.run_manual_analysis(target_date)
        
        return {
            'success': True,
            'data': results,
            'message': f'Manual analysis completed for {target_date}'
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual analysis failed: {str(e)}")

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status and next run time"""
    try:
        next_run = market_close_scheduler.get_next_run_time()
        
        return {
            'success': True,
            'data': {
                'scheduler_running': market_close_scheduler.scheduler.running,
                'next_run_time': next_run,
                'timezone': 'Asia/Kolkata',
                'scheduled_times': ['15:45 IST (Primary)', '16:00 IST (Backup)']
            },
            'message': 'Scheduler status retrieved successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")

@router.post("/scheduler/start")
async def start_scheduler():
    """Start the market close scheduler"""
    try:
        market_close_scheduler.start_scheduler()
        
        return {
            'success': True,
            'data': {
                'scheduler_started': True,
                'next_run_time': market_close_scheduler.get_next_run_time()
            },
            'message': 'Market close scheduler started successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the market close scheduler"""
    try:
        market_close_scheduler.stop_scheduler()
        
        return {
            'success': True,
            'data': {
                'scheduler_stopped': True
            },
            'message': 'Market close scheduler stopped successfully'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")
