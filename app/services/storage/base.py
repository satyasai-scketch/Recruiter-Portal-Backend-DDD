"""
Abstract base class for storage services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class StorageService(ABC):
    """Abstract base class for storage services."""
    
    @abstractmethod
    def upload_file(self, file_bytes: bytes, key: str, content_type: str = None, metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Upload file bytes to storage.
        
        Args:
            file_bytes: File content as bytes
            key: Storage key/path for the file
            content_type: MIME type of the file
            metadata: Additional metadata to store with the file
            
        Returns:
            Dictionary with upload result:
            - success: Boolean indicating if upload was successful
            - url: URL of the uploaded file (or None)
            - error: Error message if upload failed (or None)
        """
        pass
    
    @abstractmethod
    def file_exists(self, key: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            key: Storage key/path for the file
            
        Returns:
            True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_file(self, key: str) -> Dict[str, Any]:
        """
        Delete file from storage.
        
        Args:
            key: Storage key/path for the file
            
        Returns:
            Dictionary with deletion result:
            - success: Boolean indicating if deletion was successful
            - error: Error message if deletion failed (or None)
        """
        pass
    
    @abstractmethod
    def get_file_url(self, key: str) -> str:
        """
        Get the public URL for a file.
        
        Args:
            key: Storage key/path for the file
            
        Returns:
            Public URL for the file
        """
        pass
