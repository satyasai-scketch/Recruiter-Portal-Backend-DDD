"""
Storage factory for creating storage service instances based on configuration.
"""

from typing import Optional
from app.core.config import settings
from .base import StorageService
from .local_storage import LocalStorageService
from .s3_storage import S3StorageService


class StorageFactory:
    """Factory for creating storage service instances."""
    
    _instance: Optional[StorageService] = None
    
    @classmethod
    def get_storage_service(cls, storage_type: str = None) -> StorageService:
        """
        Get a storage service instance based on configuration.
        
        Args:
            storage_type: Override storage type ("local" or "s3")
            
        Returns:
            Storage service instance
            
        Raises:
            ValueError: If storage type is not supported
        """
        # Use provided type or fall back to configuration
        storage_type = storage_type or settings.STORAGE_TYPE
        
        if storage_type.lower() == "local":
            return LocalStorageService()
        elif storage_type.lower() == "s3":
            return S3StorageService()
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}. Supported types: 'local', 's3'")
    
    @classmethod
    def get_singleton_storage_service(cls, storage_type: str = None) -> StorageService:
        """
        Get a singleton storage service instance.
        
        This method maintains a single instance per storage type for efficiency.
        
        Args:
            storage_type: Override storage type ("local" or "s3")
            
        Returns:
            Singleton storage service instance
        """
        # Use provided type or fall back to configuration
        storage_type = storage_type or settings.STORAGE_TYPE
        
        # Create new instance if type changed or no instance exists
        if cls._instance is None or not isinstance(cls._instance, 
            LocalStorageService if storage_type.lower() == "local" else S3StorageService):
            cls._instance = cls.get_storage_service(storage_type)
        
        return cls._instance
    
    @classmethod
    def clear_singleton(cls):
        """Clear the singleton instance (useful for testing)."""
        cls._instance = None
    
    @classmethod
    def get_available_storage_types(cls) -> list:
        """
        Get list of available storage types.
        
        Returns:
            List of supported storage types
        """
        return ["local", "s3"]
    
    @classmethod
    def validate_storage_config(cls, storage_type: str = None) -> dict:
        """
        Validate storage configuration.
        
        Args:
            storage_type: Storage type to validate
            
        Returns:
            Dictionary with validation results
        """
        storage_type = storage_type or settings.STORAGE_TYPE
        
        result = {
            'valid': False,
            'type': storage_type,
            'errors': []
        }
        
        try:
            if storage_type.lower() == "local":
                # Validate local storage configuration
                if not hasattr(settings, 'LOCAL_STORAGE_PATH'):
                    result['errors'].append("LOCAL_STORAGE_PATH not configured")
                if not hasattr(settings, 'LOCAL_STORAGE_URL_PREFIX'):
                    result['errors'].append("LOCAL_STORAGE_URL_PREFIX not configured")
                
                if not result['errors']:
                    result['valid'] = True
                    
            elif storage_type.lower() == "s3":
                # Validate S3 configuration
                if not hasattr(settings, 'S3_BUCKET_NAME') or not settings.S3_BUCKET_NAME:
                    result['errors'].append("S3_BUCKET_NAME not configured")
                if not hasattr(settings, 'S3_REGION') or not settings.S3_REGION:
                    result['errors'].append("S3_REGION not configured")
                
                # S3 credentials are optional (can use IAM roles)
                if not result['errors']:
                    result['valid'] = True
                    
            else:
                result['errors'].append(f"Unsupported storage type: {storage_type}")
                
        except Exception as e:
            result['errors'].append(f"Configuration validation error: {str(e)}")
        
        return result
