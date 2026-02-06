"""
Chat service
"""
from .database import get_db
from .prediction_service import prediction_service

class ChatService:
    def __init__(self):
        pass
    
    async def process_message(self, message: str, user_id: int = None, session_id: str = None, db = None):
        """Process chat message"""
        # Generate a session ID if not provided
        if not session_id:
            session_id = f"session_{user_id}_{hash(message) % 10000}"
        
        # Simple response for now
        response = f"Hello! I received your message: '{message}'. How can I help you with trading?"
        
        return {
            "session_id": session_id,
            "response": response,
            "metadata": {
                "user_id": user_id,
                "message_length": len(message),
                "timestamp": "2025-10-12T12:00:00Z"
            },
            "intent": {
                "type": "general",
                "confidence": 0.8
            }
        }

chat_service = ChatService()
