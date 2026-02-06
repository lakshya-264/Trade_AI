"""
🔧 HOLDINGS API ENDPOINT
Create API endpoint to fetch user holdings
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from typing import Dict, List, Any
from datetime import datetime

from core.database_unified import User
from core.auth_dependencies import get_current_active_user

router = APIRouter(prefix="/api/v1/holdings", tags=["Holdings"])

@router.get("/user-holdings")
async def get_user_holdings(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's stock holdings"""
    try:
        # Use direct database connection to ensure correct database
        from sqlalchemy.orm import sessionmaker
        
        database_url = "sqlite:///D:/Trader_AI_WEB_V_0.3/Trader_AI_V_0.1/trader_ai.db"
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Get user ID
            if isinstance(current_user, dict):
                user_id = current_user.get('id')
            else:
                user_id = current_user.id
            
            print(f"🔍 FETCHING HOLDINGS FOR USER: {user_id}")
            
            # Get user holdings
            holdings = session.execute(text("""
                SELECT symbol, quantity, avg_price, current_price, total_value, 
                       unrealized_pnl, unrealized_pnl_percent, created_at, updated_at
                FROM holdings 
                WHERE user_id = :user_id
                ORDER BY symbol
            """), {'user_id': user_id}).fetchall()
            
            print(f"📊 FOUND {len(holdings)} HOLDINGS")
            
            # Format holdings for frontend
            formatted_holdings = []
            total_value = 0
            total_pnl = 0
            
            for holding in holdings:
                holding_data = {
                    'symbol': holding[0],
                    'quantity': holding[1],
                    'avg_price': holding[2],
                    'current_price': holding[3],
                    'total_value': holding[4],
                    'unrealized_pnl': holding[5],
                    'unrealized_pnl_percent': holding[6],
                    'created_at': holding[7],
                    'updated_at': holding[8]
                }
                
                formatted_holdings.append(holding_data)
                total_value += holding[4]
                total_pnl += holding[5]
            
            return {
                'success': True,
                'data': {
                    'holdings': formatted_holdings,
                    'summary': {
                        'total_holdings': len(formatted_holdings),
                        'total_value': total_value,
                        'total_pnl': total_pnl,
                        'total_pnl_percent': (total_pnl / total_value * 100) if total_value > 0 else 0
                    }
                },
                'message': f'Found {len(formatted_holdings)} holdings'
            }
            
        finally:
            session.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get holdings: {str(e)}")
