"""
Local file system storage service implementation.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urljoin

from app.core.config import settings
from .base import StorageService


class LocalStorageService(StorageService):
    """Local file system storage service."""
    
    def __init__(self, 
                 storage_path: str = None,
                 url_prefix: str = None):
        """
        Initialize local storage service.
        
        Args:
            storage_path: Local directory path for file storage
            url_prefix: URL prefix for serving files (e.g., "http://localhost:8000/uploads")
        """
        self.storage_path = Path(storage_path or settings.LOCAL_STORAGE_PATH)
        self.url_prefix = url_prefix or settings.LOCAL_STORAGE_URL_PREFIX
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def upload_file(self, file_bytes: bytes, key: str, content_type: str = None, metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Upload file bytes to local storage.
        
        Args:
            file_bytes: File content as bytes
            key: Storage key/path for the file (e.g., "cvs/abc123.pdf")
            content_type: MIME type of the file
            metadata: Additional metadata (ignored for local storage)
            
        Returns:
            Dictionary with upload result
        """
        result = {
            'success': False,
            'url': None,
            'error': None
        }
        
        try:
            # Create full file path
            file_path = self.storage_path / key
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            # Generate URL
            result['url'] = self.get_file_url(key)
            result['success'] = True
            
        except PermissionError:
            result['error'] = f"Permission denied writing to {file_path}"
        except OSError as e:
            result['error'] = f"File system error: {str(e)}"
        except Exception as e:
            result['error'] = f"Unexpected error during local upload: {str(e)}"
        
        return result
    
    def file_exists(self, key: str) -> bool:
        """
        Check if file exists in local storage.
        
        Args:
            key: Storage key/path for the file
            
        Returns:
            True if file exists, False otherwise
        """
        file_path = self.storage_path / key
        return file_path.exists() and file_path.is_file()
    
    def delete_file(self, key: str) -> Dict[str, Any]:
        """
        Delete file from local storage.
        
        Args:
            key: Storage key/path for the file
            
        Returns:
            Dictionary with deletion result
        """
        result = {
            'success': False,
            'error': None
        }
        
        try:
            file_path = self.storage_path / key
            
            if not file_path.exists():
                result['error'] = f"File {key} does not exist"
                return result
            
            if not file_path.is_file():
                result['error'] = f"Path {key} is not a file"
                return result
            
            file_path.unlink()
            result['success'] = True
            
        except PermissionError:
            result['error'] = f"Permission denied deleting {key}"
        except OSError as e:
            result['error'] = f"File system error: {str(e)}"
        except Exception as e:
            result['error'] = f"Unexpected error during local deletion: {str(e)}"
        
        return result
    
    def get_file_url(self, key: str) -> str:
        """
        Get the public URL for a file.
        
        Args:
            key: Storage key/path for the file
            
        Returns:
            Public URL for the file
        """
        # Remove leading slash from key if present
        clean_key = key.lstrip('/')
        return urljoin(self.url_prefix.rstrip('/') + '/', clean_key)
    
    def get_file_path(self, key: str) -> Path:
        """
        Get the local file system path for a file.
        
        Args:
            key: Storage key/path for the file
            
        Returns:
            Path object for the file
        """
        return self.storage_path / key
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about the local storage.
        
        Returns:
            Dictionary with storage information
        """
        try:
            total_size = sum(f.stat().st_size for f in self.storage_path.rglob('*') if f.is_file())
            file_count = len([f for f in self.storage_path.rglob('*') if f.is_file()])
            
            return {
                'type': 'local',
                'path': str(self.storage_path),
                'url_prefix': self.url_prefix,
                'total_size_bytes': total_size,
                'file_count': file_count,
                'exists': self.storage_path.exists()
            }
        except Exception as e:
            return {
                'type': 'local',
                'path': str(self.storage_path),
                'url_prefix': self.url_prefix,
                'error': str(e)
            }
