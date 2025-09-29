"""
Email provider factory for creating provider instances.
"""

from typing import Dict, Any
from .base import EmailProvider
from .smtp_provider import SMTPProvider
from .sendgrid_provider import SendGridProvider
from .aws_ses_provider import AWSSESProvider


class EmailProviderFactory:
    """Factory for creating email provider instances."""
    
    _providers = {
        'smtp': SMTPProvider,
        'sendgrid': SendGridProvider,
        'aws_ses': AWSSESProvider
    }
    
    @classmethod
    def create_provider(cls, provider_name: str, config: Dict[str, Any]) -> EmailProvider:
        """
        Create an email provider instance.
        
        Args:
            provider_name: Name of the provider ('smtp' or 'sendgrid')
            config: Provider-specific configuration
            
        Returns:
            EmailProvider: Provider instance
            
        Raises:
            ValueError: If provider name is not supported
        """
        provider_name = provider_name.lower()
        
        if provider_name not in cls._providers:
            raise ValueError(f"Unsupported email provider: {provider_name}")
        
        provider_class = cls._providers[provider_name]
        return provider_class(config)
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported provider names."""
        return list(cls._providers.keys())
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        Register a new email provider.
        
        Args:
            name: Provider name
            provider_class: Provider class that implements EmailProvider
        """
        cls._providers[name.lower()] = provider_class
