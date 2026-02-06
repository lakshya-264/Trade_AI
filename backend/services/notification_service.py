"""
Notification Service for WhatsApp and SMS Integration
Sends trading signals via multiple channels
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.whatsapp_api_key = os.getenv("WHATSAPP_API_KEY")
        self.whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_ID")
        self.twilio_sid = os.getenv("TWILIO_SID")
        self.twilio_token = os.getenv("TWILIO_TOKEN")
        self.twilio_phone = os.getenv("TWILIO_PHONE")
        
        # User preferences
        self.user_preferences = {
            "whatsapp_enabled": True,
            "sms_enabled": True,
            "email_enabled": True,
            "min_confidence": 0.7,
            "urgent_only": False
        }
    
    async def send_trading_signal(self, signal_data: Dict, user_phone: str = None) -> Dict:
        """Send trading signal via all enabled channels"""
        try:
            results = {
                "whatsapp": False,
                "sms": False,
                "email": False,
                "timestamp": datetime.now().isoformat()
            }
            
            # Check if signal meets criteria
            if not self._should_send_alert(signal_data):
                return {"status": "skipped", "reason": "Signal doesn't meet criteria"}
            
            # Prepare message
            message = self._format_trading_message(signal_data)
            
            # Send via WhatsApp
            if self.user_preferences["whatsapp_enabled"] and user_phone:
                results["whatsapp"] = await self._send_whatsapp_message(user_phone, message)
            
            # Send via SMS
            if self.user_preferences["sms_enabled"] and user_phone:
                results["sms"] = await self._send_sms_message(user_phone, message)
            
            # Send via Email (placeholder)
            if self.user_preferences["email_enabled"]:
                results["email"] = await self._send_email_message(signal_data, message)
            
            return {
                "status": "sent",
                "results": results,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"Error sending trading signal: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _send_whatsapp_message(self, phone: str, message: str) -> bool:
        """Send message via WhatsApp Business API"""
        try:
            if not self.whatsapp_api_key or not self.whatsapp_phone_id:
                logger.warning("WhatsApp API credentials not configured")
                return False
            
            url = f"https://graph.facebook.com/v17.0/{self.whatsapp_phone_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.whatsapp_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "text",
                "text": {"body": message}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        logger.info(f"WhatsApp message sent to {phone}")
                        return True
                    else:
                        logger.error(f"WhatsApp API error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False
    
    async def _send_sms_message(self, phone: str, message: str) -> bool:
        """Send message via Twilio SMS"""
        try:
            if not all([self.twilio_sid, self.twilio_token, self.twilio_phone]):
                logger.warning("Twilio credentials not configured")
                return False
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
            
            auth = aiohttp.BasicAuth(self.twilio_sid, self.twilio_token)
            
            data = {
                "From": self.twilio_phone,
                "To": phone,
                "Body": message
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, auth=auth, data=data) as response:
                    if response.status in [200, 201]:
                        logger.info(f"SMS sent to {phone}")
                        return True
                    else:
                        logger.error(f"Twilio API error: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
    
    async def _send_email_message(self, signal_data: Dict, message: str) -> bool:
        """Send message via email (placeholder implementation)"""
        try:
            # This would integrate with an email service like SendGrid, AWS SES, etc.
            logger.info(f"Email notification: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _should_send_alert(self, signal_data: Dict) -> bool:
        """Check if alert should be sent based on criteria"""
        try:
            confidence = signal_data.get('confidence', 0)
            action = signal_data.get('action', 'HOLD')
            urgency = signal_data.get('urgency', 'LOW')
            
            # Check minimum confidence
            if confidence < self.user_preferences["min_confidence"]:
                return False
            
            # Check if urgent only mode
            if self.user_preferences["urgent_only"] and urgency != 'HIGH':
                return False
            
            # Check if action is significant
            if action in ['HOLD', 'NEUTRAL']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking alert criteria: {e}")
            return False
    
    def _format_trading_message(self, signal_data: Dict) -> str:
        """Format trading signal into readable message"""
        try:
            symbol = signal_data.get('symbol', 'N/A')
            action = signal_data.get('action', 'HOLD')
            signal = signal_data.get('signal', 'HOLD')
            confidence = signal_data.get('confidence', 0)
            current_price = signal_data.get('current_price', 0)
            reasoning = signal_data.get('reasoning', 'No reasoning provided')
            urgency = signal_data.get('urgency', 'LOW')
            risk_level = signal_data.get('risk_level', 'MEDIUM')
            
            # Format price
            price_str = f"₹{current_price:,.2f}" if current_price > 0 else "N/A"
            
            # Format confidence
            confidence_str = f"{confidence:.1%}"
            
            # Create emoji based on action
            emoji_map = {
                'STRONG_BUY': '🚀',
                'BUY': '📈',
                'STRONG_SELL': '📉',
                'SELL': '🔻',
                'HOLD': '⏸️'
            }
            emoji = emoji_map.get(action, '📊')
            
            # Create urgency indicator
            urgency_map = {
                'HIGH': '🔥',
                'MEDIUM': '⚡',
                'LOW': '💡'
            }
            urgency_emoji = urgency_map.get(urgency, '💡')
            
            # Create risk indicator
            risk_map = {
                'HIGH': '🔴',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }
            risk_emoji = risk_map.get(risk_level, '🟡')
            
            message = f"""
{emoji} *TRADING SIGNAL* {emoji}

📊 *Symbol:* {symbol}
💰 *Current Price:* {price_str}
🎯 *Action:* {action}
📈 *Signal:* {signal}
🎲 *Confidence:* {confidence_str}
{urgency_emoji} *Urgency:* {urgency}
{risk_emoji} *Risk Level:* {risk_level}

💭 *Reasoning:*
{reasoning}

⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ *Disclaimer:* This is for educational purposes only. Please do your own research before trading.
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return f"Trading signal for {signal_data.get('symbol', 'N/A')}: {signal_data.get('action', 'HOLD')}"
    
    def update_user_preferences(self, preferences: Dict):
        """Update user notification preferences"""
        try:
            self.user_preferences.update(preferences)
            logger.info("User preferences updated")
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
    
    def get_user_preferences(self) -> Dict:
        """Get current user preferences"""
        return self.user_preferences.copy()
    
    async def send_bulk_notifications(self, signals: List[Dict], user_phones: List[str]) -> Dict:
        """Send notifications to multiple users"""
        try:
            results = {
                "total_signals": len(signals),
                "total_users": len(user_phones),
                "successful": 0,
                "failed": 0,
                "results": []
            }
            
            for signal in signals:
                for phone in user_phones:
                    result = await self.send_trading_signal(signal, phone)
                    if result.get("status") == "sent":
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
                    
                    results["results"].append({
                        "symbol": signal.get("symbol"),
                        "phone": phone,
                        "status": result.get("status"),
                        "timestamp": datetime.now().isoformat()
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending bulk notifications: {e}")
            return {"error": str(e)}
    
    async def test_notification(self, phone: str) -> Dict:
        """Send test notification to verify setup"""
        try:
            test_signal = {
                "symbol": "TEST",
                "action": "BUY",
                "signal": "BUY",
                "confidence": 0.8,
                "current_price": 100.0,
                "reasoning": "This is a test notification to verify your setup.",
                "urgency": "LOW",
                "risk_level": "LOW"
            }
            
            return await self.send_trading_signal(test_signal, phone)
            
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            return {"status": "error", "error": str(e)}
