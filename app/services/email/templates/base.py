"""
Base email template class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class EmailTemplate(ABC):
    """Abstract base class for email templates."""
    
    @abstractmethod
    def get_subject(self, **kwargs) -> str:
        """Get the email subject."""
        pass
    
    @abstractmethod
    def get_html_content(self, **kwargs) -> str:
        """Get the HTML email content."""
        pass
    
    @abstractmethod
    def get_text_content(self, **kwargs) -> str:
        """Get the plain text email content."""
        pass
