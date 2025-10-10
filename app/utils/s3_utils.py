"""
S3 utilities for CV file storage and retrieval.
"""

import boto3
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import settings


class S3Client:
    """S3 client wrapper for CV file operations."""
    
    def __init__(self, 
                 bucket_name: Optional[str] = None,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None,
                 aws_region: Optional[str] = None):
        """
        Initialize S3 client.
        
        Args:
            bucket_name: S3 bucket name (defaults to settings)
            aws_access_key_id: AWS access key (defaults to settings)
            aws_secret_access_key: AWS secret key (defaults to settings)
            aws_region: AWS region (defaults to settings)
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
    
    def upload_file_bytes(self, 
                         file_bytes: bytes, 
                         s3_key: str, 
                         content_type: Optional[str] = None,
                         metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload file bytes to S3.
        
        Args:
            file_bytes: File content as bytes
            s3_key: S3 object key
            content_type: MIME type of the file
            metadata: Additional metadata to store with the object
            
        Returns:
            Dictionary with upload result:
            - success: Boolean indicating if upload was successful
            - url: S3 URL of the uploaded file (or None)
            - error: Error message if upload failed (or None)
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
                'Key': s3_key,
                'Body': file_bytes
            }
            
            if content_type:
                upload_params['ContentType'] = content_type
            
            if metadata:
                upload_params['Metadata'] = metadata
            
            # Upload file
            self.s3_client.put_object(**upload_params)
            
            # Generate URL
            result['url'] = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
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
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if file exists in S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            # Re-raise other errors
            raise
    
    def delete_file(self, s3_key: str) -> Dict[str, Any]:
        """
        Delete file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dictionary with deletion result:
            - success: Boolean indicating if deletion was successful
            - error: Error message if deletion failed (or None)
        """
        result = {
            'success': False,
            'error': None
        }
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            result['success'] = True
        except ClientError as e:
            result['error'] = f"S3 deletion failed: {e.response['Error']['Message']}"
        except Exception as e:
            result['error'] = f"Unexpected error during S3 deletion: {str(e)}"
        
        return result


def upload_cv_to_s3(file_bytes: bytes, 
                   s3_key: str, 
                   content_type: Optional[str] = None,
                   metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Convenience function to upload CV file to S3.
    
    Args:
        file_bytes: File content as bytes
        s3_key: S3 object key
        content_type: MIME type of the file
        metadata: Additional metadata to store with the object
        
    Returns:
        Dictionary with upload result (see S3Client.upload_file_bytes)
    """
    s3_client = S3Client()
    return s3_client.upload_file_bytes(file_bytes, s3_key, content_type, metadata)


def check_cv_exists_in_s3(s3_key: str) -> bool:
    """
    Convenience function to check if CV file exists in S3.
    
    Args:
        s3_key: S3 object key
        
    Returns:
        True if file exists, False otherwise
    """
    s3_client = S3Client()
    return s3_client.file_exists(s3_key)


def delete_cv_from_s3(s3_key: str) -> Dict[str, Any]:
    """
    Convenience function to delete CV file from S3.
    
    Args:
        s3_key: S3 object key
        
    Returns:
        Dictionary with deletion result (see S3Client.delete_file)
    """
    s3_client = S3Client()
    return s3_client.delete_file(s3_key)
