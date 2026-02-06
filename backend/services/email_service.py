"""
Email Notification Service
Send alert notifications via email using SendGrid
"""

import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Check if SendGrid is available
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning("SendGrid not installed. Email notifications disabled. Install with: pip install sendgrid")

class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'alerts@traderai.com')
        self.enabled = SENDGRID_AVAILABLE and bool(self.api_key)
        
        if not self.enabled:
            logger.info("Email service disabled. Set SENDGRID_API_KEY environment variable to enable.")
    
    def send_alert_email(
        self,
        to_email: str,
        alert_data: Dict,
        subject: Optional[str] = None
    ) -> bool:
        """
        Send alert notification email
        
        Args:
            to_email: Recipient email address
            alert_data: Alert information (symbol, price, condition, etc.)
            subject: Optional custom subject
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Email service not enabled, skipping email")
            return False
        
        try:
            # Generate subject
            if not subject:
                symbol = alert_data.get('symbol', 'Stock')
                condition = alert_data.get('condition', 'triggered')
                subject = f"🔔 Alert: {symbol} {condition}"
            
            # Generate HTML content
            html_content = self._generate_html_email(alert_data)
            
            # Create email
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Send email
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)
            
            if response.status_code == 202:
                logger.info(f"✅ Email sent to {to_email}: {subject}")
                return True
            else:
                logger.error(f"Failed to send email. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _generate_html_email(self, alert_data: Dict) -> str:
        """Generate HTML email content"""
        symbol = alert_data.get('symbol', 'Stock')
        current_price = alert_data.get('current_price', 0)
        target_price = alert_data.get('target_price', 0)
        condition = alert_data.get('condition', 'triggered')
        alert_type = alert_data.get('alert_type', 'price_level')
        timestamp = alert_data.get('timestamp', '')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .content {{
                    padding: 30px;
                }}
                .alert-box {{
                    background-color: #f8f9fa;
                    border-left: 4px solid #667eea;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .price {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #667eea;
                    margin: 10px 0;
                }}
                .detail {{
                    font-size: 16px;
                    color: #666;
                    margin: 8px 0;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #999;
                }}
                .button {{
                    display: inline-block;
                    background-color: #667eea;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 Price Alert Triggered!</h1>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <h2 style="margin-top: 0; color: #333;">{symbol}</h2>
                        <div class="price">₹{current_price:.2f}</div>
                        <div class="detail">
                            <strong>Condition:</strong> Price {condition} ₹{target_price:.2f}
                        </div>
                        <div class="detail">
                            <strong>Alert Type:</strong> {alert_type.replace('_', ' ').title()}
                        </div>
                        <div class="detail">
                            <strong>Time:</strong> {timestamp}
                        </div>
                    </div>
                    <p style="color: #666;">
                        Your price alert for <strong>{symbol}</strong> has been triggered. 
                        The current price has {condition} your target level.
                    </p>
                    <a href="http://localhost:3000/comprehensive-trading-pro" class="button">
                        View Chart →
                    </a>
                </div>
                <div class="footer">
                    <p>Trader AI - Intelligent Stock Market Analysis</p>
                    <p>You received this email because you set up an alert for {symbol}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

# Singleton instance
email_service = EmailService()

