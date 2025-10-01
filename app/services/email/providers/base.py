"""
Base email provider interface for implementing different email services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class EmailProvider(ABC):
    """Abstract base class for email providers."""
    
    @abstractmethod
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send an email with HTML and optional text content.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Optional plain text content
            from_email: Sender email (if different from default)
            from_name: Sender name (if different from default)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Validate that the provider is properly configured.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the email provider.
        
        Returns:
            str: Provider name
        """
        pass
