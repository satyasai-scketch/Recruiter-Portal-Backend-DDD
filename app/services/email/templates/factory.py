"""
Email template factory for creating template instances.
"""

from typing import Dict, Type
from .base import EmailTemplate
from .password_reset import PasswordResetTemplate
from .welcome import WelcomeTemplate


class EmailTemplateFactory:
    """Factory for creating email template instances."""
    
    _templates: Dict[str, Type[EmailTemplate]] = {
        'password_reset': PasswordResetTemplate,
        'welcome': WelcomeTemplate
    }
    
    @classmethod
    def create_template(cls, template_name: str) -> EmailTemplate:
        """
        Create an email template instance.
        
        Args:
            template_name: Name of the template
            
        Returns:
            EmailTemplate: Template instance
            
        Raises:
            ValueError: If template name is not found
        """
        if template_name not in cls._templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template_class = cls._templates[template_name]
        return template_class()
    
    @classmethod
    def get_available_templates(cls) -> list:
        """Get list of available template names."""
        return list(cls._templates.keys())
    
    @classmethod
    def register_template(cls, name: str, template_class: Type[EmailTemplate]):
        """
        Register a new email template.
        
        Args:
            name: Template name
            template_class: Template class that implements EmailTemplate
        """
        cls._templates[name] = template_class
