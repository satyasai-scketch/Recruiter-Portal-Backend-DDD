"""
SMTP email provider implementation.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from .base import EmailProvider

logger = logging.getLogger(__name__)


class SMTPProvider(EmailProvider):
    """SMTP email provider implementation."""
    
    def __init__(self, config: dict):
        """
        Initialize SMTP provider with configuration.
        
        Args:
            config: Dictionary containing SMTP configuration
        """
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_username = config.get('smtp_username')
        self.smtp_password = config.get('smtp_password')
        self.from_email = config.get('from_email', 'noreply@recruiterai.com')
        self.from_name = config.get('from_name', 'Recruiter AI')
        self.use_tls = config.get('use_tls', True)
    
    def get_provider_name(self) -> str:
        """Get the name of the email provider."""
        return "SMTP"
    
    def validate_configuration(self) -> bool:
        """Validate that the provider is properly configured."""
        required_fields = ['smtp_server', 'smtp_port']
        for field in required_fields:
            if not getattr(self, field):
                logger.error(f"SMTP configuration missing required field: {field}")
                return False
        
        # For authenticated SMTP, username and password are required
        if self.smtp_username and not self.smtp_password:
            logger.error("SMTP username provided but password is missing")
            return False
        
        return True
    
    def _create_connection(self) -> smtplib.SMTP:
        """Create SMTP connection with proper authentication."""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """Send email using SMTP."""
        try:
            # Use provided from_email/from_name or defaults
            sender_email = from_email or self.from_email
            sender_name = from_name or self.from_name
            
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{sender_name} <{sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            server = self._create_connection()
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email} via SMTP")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via SMTP: {e}")
            return False
