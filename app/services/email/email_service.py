"""
Main email service that manages different email providers and templates.
"""

import logging
from typing import Optional, Dict, Any

from app.core.config import settings
from .providers.base import EmailProvider
from .providers.factory import EmailProviderFactory
from .templates.factory import EmailTemplateFactory

logger = logging.getLogger(__name__)


class EmailService:
    """Main email service that manages providers and templates."""
    
    def __init__(self, provider_name: Optional[str] = None):
        """
        Initialize email service with specified provider.
        
        Args:
            provider_name: Name of the email provider to use ('smtp' or 'sendgrid')
        """
        self.provider_name = provider_name or getattr(settings, 'email_provider', 'smtp')
        self.provider = self._create_provider()
        self.templates = {
            'password_reset': EmailTemplateFactory.create_template('password_reset'),
            'welcome': EmailTemplateFactory.create_template('welcome'),
            'mfa_otp': EmailTemplateFactory.create_template('mfa_otp'),
            'backup_codes': EmailTemplateFactory.create_template('backup_codes')
        }
    
    def _create_provider(self) -> EmailProvider:
        """Create email provider based on configuration."""
        if self.provider_name.lower() == 'sendgrid':
            config = {
                'api_key': getattr(settings, 'sendgrid_api_key', ''),
                'from_email': getattr(settings, 'from_email', 'noreply@recruiterai.com'),
                'from_name': getattr(settings, 'from_name', 'Recruiter AI')
            }
        elif self.provider_name.lower() == 'aws_ses':
            config = {
                'aws_access_key_id': getattr(settings, 'aws_access_key_id', ''),
                'aws_secret_access_key': getattr(settings, 'aws_secret_access_key', ''),
                'aws_region': getattr(settings, 'aws_region', 'us-east-1'),
                'from_email': getattr(settings, 'from_email', 'noreply@recruiterai.com'),
                'from_name': getattr(settings, 'from_name', 'Recruiter AI')
            }
        elif self.provider_name.lower() == 'smtp':
            config = {
                'smtp_server': getattr(settings, 'smtp_server', 'smtp.gmail.com'),
                'smtp_port': getattr(settings, 'smtp_port', 587),
                'smtp_username': getattr(settings, 'smtp_username', ''),
                'smtp_password': getattr(settings, 'smtp_password', ''),
                'from_email': getattr(settings, 'from_email', 'noreply@recruiterai.com'),
                'from_name': getattr(settings, 'from_name', 'Recruiter AI'),
                'use_tls': getattr(settings, 'smtp_use_tls', True)
            }
        else:
            raise ValueError(f"Unsupported email provider: {self.provider_name}")
        
        return EmailProviderFactory.create_provider(self.provider_name, config)
    
    def validate_configuration(self) -> bool:
        """Validate email service configuration."""
        return self.provider.validate_configuration()
    
    def send_template_email(
        self, 
        template_name: str, 
        to_email: str, 
        **template_kwargs
    ) -> bool:
        """
        Send email using a predefined template.
        
        Args:
            template_name: Name of the template to use
            to_email: Recipient email address
            **template_kwargs: Template-specific parameters
            
        Returns:
            bool: True if email was sent successfully
        """
        if template_name not in self.templates:
            logger.error(f"Template '{template_name}' not found")
            return False
        
        template = self.templates[template_name]
        
        try:
            subject = template.get_subject(**template_kwargs)
            html_content = template.get_html_content(**template_kwargs)
            text_content = template.get_text_content(**template_kwargs)
            
            logger.info(f"Attempting to send {template_name} email to {to_email}")
            result = self.provider.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if result:
                logger.info(f"Successfully sent {template_name} email to {to_email}")
            else:
                logger.error(f"Failed to send {template_name} email to {to_email}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send template email '{template_name}' to {to_email}: {e}")
            return False
    
    def send_custom_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send custom email with provided content.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Optional plain text content
            from_email: Sender email (if different from default)
            from_name: Sender name (if different from default)
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            return self.provider.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_email=from_email,
                from_name=from_name
            )
        except Exception as e:
            logger.error(f"Failed to send custom email: {e}")
            return False
    
    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str = None) -> bool:
        """Send password reset email."""
        reset_url = f"{getattr(settings, 'frontend_url', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        return self.send_template_email(
            template_name='password_reset',
            to_email=to_email,
            user_name=user_name,
            reset_url=reset_url
        )
    
    def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send welcome email to new users."""
        return self.send_template_email(
            template_name='welcome',
            to_email=to_email,
            user_name=user_name
        )
    
    def send_mfa_otp_email(self, to_email: str, otp_code: str, user_name: str = None, expiry_minutes: int = 10) -> bool:
        """Send MFA OTP email."""
        return self.send_template_email(
            template_name='mfa_otp',
            to_email=to_email,
            otp_code=otp_code,
            user_name=user_name or 'User',
            expiry_minutes=expiry_minutes
        )
    
    def send_backup_codes_email(self, to_email: str, backup_codes: list, user_name: str = None) -> bool:
        """Send backup codes email."""
        return self.send_template_email(
            template_name='backup_codes',
            to_email=to_email,
            backup_codes=backup_codes,
            user_name=user_name or 'User'
        )
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current email provider."""
        return {
            'provider_name': self.provider.get_provider_name(),
            'configuration_valid': self.validate_configuration()
        }


# Global email service instance
email_service = EmailService()
