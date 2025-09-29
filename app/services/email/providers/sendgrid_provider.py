"""
SendGrid email provider implementation.
"""

import logging
from typing import Optional

try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

from .base import EmailProvider

logger = logging.getLogger(__name__)


class SendGridProvider(EmailProvider):
    """SendGrid email provider implementation."""
    
    def __init__(self, config: dict):
        """
        Initialize SendGrid provider with configuration.
        
        Args:
            config: Dictionary containing SendGrid configuration
        """
        if not SENDGRID_AVAILABLE:
            raise ImportError("SendGrid package not installed. Install with: pip install sendgrid")
        
        self.api_key = config.get('api_key')
        self.from_email = config.get('from_email', 'noreply@recruiterai.com')
        self.from_name = config.get('from_name', 'Recruiter AI')
        
        if self.api_key:
            self.sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
        else:
            self.sg = None
    
    def get_provider_name(self) -> str:
        """Get the name of the email provider."""
        return "SendGrid"
    
    def validate_configuration(self) -> bool:
        """Validate that the provider is properly configured."""
        if not SENDGRID_AVAILABLE:
            logger.error("SendGrid package not installed")
            return False
        
        if not self.api_key:
            logger.error("SendGrid API key is required")
            return False
        
        if not self.from_email:
            logger.error("SendGrid from_email is required")
            return False
        
        return True
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """Send email using SendGrid."""
        try:
            if not self.sg:
                logger.error("SendGrid client not initialized")
                return False
            
            # Use provided from_email/from_name or defaults
            sender_email = from_email or self.from_email
            sender_name = from_name or self.from_name
            
            # Create email
            from_email_obj = Email(sender_email, sender_name)
            to_email_obj = To(to_email)
            
            # Create content
            if text_content:
                # Send both HTML and text
                mail = Mail(
                    from_email=from_email_obj,
                    to_emails=to_email_obj,
                    subject=subject,
                    html_content=Content("text/html", html_content),
                    plain_text_content=Content("text/plain", text_content)
                )
            else:
                # Send only HTML
                mail = Mail(
                    from_email=from_email_obj,
                    to_emails=to_email_obj,
                    subject=subject,
                    html_content=Content("text/html", html_content)
                )
            
            # Send email
            response = self.sg.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email} via SendGrid")
                return True
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via SendGrid: {e}")
            return False
