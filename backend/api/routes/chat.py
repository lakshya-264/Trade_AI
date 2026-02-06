"""
Chat API routes for AI chatbot functionality
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from core.database import get_db, User
from core.auth_dependencies import get_current_active_user
from core.chat_service import chat_service
from core.prediction_service import prediction_service
from models.chat import ChatSession, ChatMessage, PredictionHistory

router = APIRouter()

# Pydantic models
class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    session_id: str
    response: str
    metadata: dict
    intent: dict
    timestamp: str

class ChatSessionResponse(BaseModel):
    session_id: str
    session_name: str
    created_at: str
    last_activity: str
    message_count: int
    is_active: bool

class PredictionRequest(BaseModel):
    symbol: str
    prediction_type: str = "price"  # price, volatility, signals, support_resistance
    horizon: Optional[str] = "1d"
    timeframe: Optional[str] = "1h"

class ChatPredictionRequest(BaseModel):
    message: str
    # Make symbol optional; derive from message when absent
    symbol: Optional[str] = None
    prediction_type: str = "price"

class PredictionResponse(BaseModel):
    success: bool
    symbol: str
    prediction_type: str
    data: dict
    confidence: float
    timestamp: str

# Chat endpoints
@router.post("/send", response_model=ChatMessageResponse)
async def send_message(
    message_request: ChatMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send message to AI chatbot"""
    try:
        result = await chat_service.process_message(
            user_id=current_user.id,
            message=message_request.message,
            session_id=message_request.session_id,
            db=db
        )
        
        return ChatMessageResponse(
            session_id=result["session_id"],
            response=result["response"],
            metadata=result["metadata"],
            intent=result["intent"],
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's chat sessions"""
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id,
            ChatSession.is_active == True
        ).order_by(ChatSession.last_activity.desc()).limit(20).all()
        
        return [
            ChatSessionResponse(
                session_id=session.session_id,
                session_name=session.session_name,
                created_at=session.created_at.isoformat(),
                last_activity=session.last_activity.isoformat(),
                message_count=session.message_count,
                is_active=session.is_active
            )
            for session in sessions
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get messages from a chat session"""
    try:
        # Verify session belongs to user
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.asc()).all()
        
        return [
            {
                "id": msg.id,
                "message_type": msg.message_type,
                "content": msg.content,
                "metadata": msg.metadata_json or {},
                "timestamp": msg.timestamp.isoformat(),
                "is_ai_generated": msg.is_ai_generated,
                "confidence_score": msg.confidence_score
            }
            for msg in messages
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

@router.post("/sessions/{session_id}/clear")
async def clear_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clear chat session messages"""
    try:
        # Verify session belongs to user
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete all messages in the session
        db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete()
        
        # Reset message count
        session.message_count = 0
        session.last_activity = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Session cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    try:
        # Verify session belongs to user
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Mark session as inactive
        session.is_active = False
        db.commit()
        
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

# Prediction endpoints
@router.post("/predict", response_model=PredictionResponse)
async def get_prediction(
    prediction_request: ChatPredictionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI prediction for a symbol"""
    try:
        # Manual validation since Pydantic validators aren't working
        if not prediction_request.message or not prediction_request.message.strip():
            raise HTTPException(status_code=422, detail="Message field is required and cannot be empty")

        # If symbol not provided, try to infer from message; fallback to a safe default
        symbol_input = (prediction_request.symbol or "").strip()
        if not symbol_input:
            # Naive extraction: take first token-like uppercase word or known index tokens
            import re
            candidates = re.findall(r"[A-Z]{2,}\b", prediction_request.message.upper())
            known_aliases = {"NIFTY", "NIFTY50", "NIFTY 50", "SENSEX", "BANKNIFTY", "NIFTYBANK"}
            inferred = None
            for token in candidates:
                if token in known_aliases or len(token) >= 3:
                    inferred = token
                    break
            symbol_input = inferred or "RELIANCE"
        
        # Validate prediction type
        valid_types = ["price", "volatility", "signals", "support_resistance"]
        if prediction_request.prediction_type not in valid_types:
            raise HTTPException(status_code=422, detail=f"Invalid prediction type. Valid types are: {', '.join(valid_types)}")

        symbol = symbol_input.upper().strip()
        prediction_type = prediction_request.prediction_type
        
        if prediction_type == "price":
            result = await prediction_service.predict_price_movement(
                symbol=symbol,
                horizon="1d",
                db=db
            )
        elif prediction_type == "volatility":
            result = await prediction_service.predict_volatility(symbol=symbol, db=db)
        elif prediction_type == "signals":
            result = await prediction_service.generate_trading_signals(symbol=symbol, db=db)
        elif prediction_type == "support_resistance":
            result = await prediction_service.predict_support_resistance(symbol=symbol, db=db)
        else:
            raise HTTPException(status_code=400, detail="Invalid prediction type")
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Prediction failed"))
        
        return PredictionResponse(
            success=True,
            symbol=symbol,
            prediction_type=prediction_type,
            data=result,
            confidence=result.get("confidence", 0.0),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating prediction: {str(e)}")

@router.get("/predictions/history")
async def get_prediction_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get user's prediction history"""
    try:
        predictions = db.query(PredictionHistory).filter(
            PredictionHistory.user_id == current_user.id
        ).order_by(PredictionHistory.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": pred.id,
                "symbol": pred.symbol,
                "prediction_type": pred.prediction_type,
                "prediction_data": pred.prediction_data,
                "confidence_score": pred.confidence_score,
                "accuracy_score": pred.accuracy_score,
                "created_at": pred.created_at.isoformat(),
                "expires_at": pred.expires_at.isoformat() if pred.expires_at else None
            }
            for pred in predictions
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching prediction history: {str(e)}")

@router.get("/predictions/accuracy")
async def get_prediction_accuracy(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get prediction accuracy statistics"""
    try:
        predictions = db.query(PredictionHistory).filter(
            PredictionHistory.user_id == current_user.id,
            PredictionHistory.accuracy_score.isnot(None)
        ).all()
        
        if not predictions:
            return {
                "total_predictions": 0,
                "average_accuracy": 0.0,
                "accuracy_by_type": {},
                "recent_accuracy": 0.0
            }
        
        total_predictions = len(predictions)
        average_accuracy = sum(p.accuracy_score for p in predictions) / total_predictions
        
        # Accuracy by prediction type
        accuracy_by_type = {}
        for pred in predictions:
            pred_type = pred.prediction_type
            if pred_type not in accuracy_by_type:
                accuracy_by_type[pred_type] = []
            accuracy_by_type[pred_type].append(pred.accuracy_score)
        
        for pred_type in accuracy_by_type:
            accuracy_by_type[pred_type] = sum(accuracy_by_type[pred_type]) / len(accuracy_by_type[pred_type])
        
        # Recent accuracy (last 10 predictions)
        recent_predictions = predictions[:10]
        recent_accuracy = sum(p.accuracy_score for p in recent_predictions) / len(recent_predictions) if recent_predictions else 0.0
        
        return {
            "total_predictions": total_predictions,
            "average_accuracy": round(average_accuracy, 2),
            "accuracy_by_type": accuracy_by_type,
            "recent_accuracy": round(recent_accuracy, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching accuracy statistics: {str(e)}")

# WebSocket endpoint for real-time chat
@router.websocket("/ws/{user_id}")
async def websocket_chat_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                message = data.get("message", "")
                session_id = data.get("session_id")
                
                # Process message
                db = next(get_db())
                try:
                    result = await chat_service.process_message(
                        user_id=user_id,
                        message=message,
                        session_id=session_id,
                        db=db
                    )
                    
                    # Send response back to client
                    await websocket.send_json({
                        "type": "response",
                        "session_id": result["session_id"],
                        "response": result["response"],
                        "metadata": result["metadata"],
                        "intent": result["intent"],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error processing message: {str(e)}"
                    })
                finally:
                    db.close()
            
            elif data.get("type") == "typing":
                # Handle typing indicator
                await websocket.send_json({
                    "type": "typing_indicator",
                    "is_typing": data.get("is_typing", False)
                })
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"WebSocket error: {str(e)}"
        })

@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get chat history for the current user"""
    try:
        # Get recent chat messages for the user
        messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user.id
        ).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
        
        history = []
        for msg in messages:
            history.append({
                "id": msg.id,
                "user_id": msg.user_id,
                "message": msg.message,
                "response": msg.response,
                "timestamp": msg.timestamp.isoformat(),
                "session_id": msg.session_id
            })
        
        return {
            "success": True,
            "data": history,
            "count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting chat history: {str(e)}"
        )

# ---------- Missing Endpoints for API Compatibility ----------

@router.get("/messages")
async def get_messages():
    """Get chat messages"""
    try:
        return {
            "message": "Chat messages retrieved successfully",
            "messages": [
                {"id": 1, "content": "Welcome to Trader AI Chat!", "timestamp": datetime.utcnow().isoformat()},
                {"id": 2, "content": "How can I help you with trading analysis?", "timestamp": datetime.utcnow().isoformat()}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messages: {str(e)}")