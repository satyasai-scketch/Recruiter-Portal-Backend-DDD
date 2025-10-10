"""
S3 storage service implementation.
"""

import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings
from .base import StorageService


class S3StorageService(StorageService):
    """S3 storage service implementation."""
    
    def __init__(self, 
                 bucket_name: Optional[str] = None,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 aws_region: Optional[str] = None):
        """
        Initialize S3 storage service.
        
        Args:
            bucket_name: S3 bucket name
            aws_access_key_id: AWS access key
            aws_secret_access_key: AWS secret key
            aws_region: AWS region
        """
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self.aws_access_key_id = aws_access_key_id or settings.S3_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.S3_SECRET_ACCESS_KEY
        self.aws_region = aws_region or settings.S3_REGION
        
        # Initialize S3 client
        if self.aws_access_key_id and self.aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
        else:
            # Use default AWS credentials (IAM role, environment variables, etc.)
            self.s3_client = boto3.client('s3', region_name=self.aws_region)
    
    def upload_file(self, file_bytes: bytes, key: str, content_type: str = None, metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Upload file bytes to S3.
        
        Args:
            file_bytes: File content as bytes
            key: S3 object key
            content_type: MIME type of the file
            metadata: Additional metadata to store with the object
            
        Returns:
            Dictionary with upload result
        """
        result = {
            'success': False,
            'url': None,
            'error': None
        }
        
        try:
            # Prepare upload parameters
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': key,
                'Body': file_bytes
            }
            
            if content_type:
                upload_params['ContentType'] = content_type
            
            if metadata:
                upload_params['Metadata'] = metadata
            
            # Upload file
            self.s3_client.put_object(**upload_params)
            
            # Generate URL
            result['url'] = self.get_file_url(key)
            result['success'] = True
            
        except NoCredentialsError:
            result['error'] = "AWS credentials not found"
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                result['error'] = f"S3 bucket '{self.bucket_name}' does not exist"
            elif error_code == 'AccessDenied':
                result['error'] = "Access denied to S3 bucket"
            else:
                result['error'] = f"S3 upload failed: {e.response['Error']['Message']}"
        except Exception as e:
            result['error'] = f"Unexpected error during S3 upload: {str(e)}"
        
        return result
    
    def file_exists(self, key: str) -> bool:
        """
        Check if file exists in S3.
        
        Args:
            key: S3 object key
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            # Re-raise other errors
            raise
    
    def delete_file(self, key: str) -> Dict[str, Any]:
        """
        Delete file from S3.
        
        Args:
            key: S3 object key
            
        Returns:
            Dictionary with deletion result
        """
        result = {
            'success': False,
            'error': None
        }
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            result['success'] = True
        except ClientError as e:
            result['error'] = f"S3 deletion failed: {e.response['Error']['Message']}"
        except Exception as e:
            result['error'] = f"Unexpected error during S3 deletion: {str(e)}"
        
        return result
    
    def get_file_url(self, key: str) -> str:
        """
        Get the public URL for a file.
        
        Args:
            key: S3 object key
            
        Returns:
            Public URL for the file
        """
        return f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{key}"
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about the S3 storage.
        
        Returns:
            Dictionary with storage information
        """
        try:
            # Try to get bucket location
            location = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            region = location.get('LocationConstraint', 'us-east-1')
            
            return {
                'type': 's3',
                'bucket_name': self.bucket_name,
                'region': region,
                'url_prefix': f"https://{self.bucket_name}.s3.{region}.amazonaws.com"
            }
        except ClientError as e:
            return {
                'type': 's3',
                'bucket_name': self.bucket_name,
                'region': self.aws_region,
                'error': f"S3 error: {e.response['Error']['Message']}"
            }
        except Exception as e:
            return {
                'type': 's3',
                'bucket_name': self.bucket_name,
                'region': self.aws_region,
                'error': str(e)
            }
