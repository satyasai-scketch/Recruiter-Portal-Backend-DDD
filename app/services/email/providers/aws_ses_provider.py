"""
AWS SES email provider implementation (example).
"""

import logging
from typing import Optional

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_SES_AVAILABLE = True
except ImportError:
    AWS_SES_AVAILABLE = False

from .base import EmailProvider

logger = logging.getLogger(__name__)


class AWSSESProvider(EmailProvider):
    """AWS SES email provider implementation."""
    
    def __init__(self, config: dict):
        """
        Initialize AWS SES provider with configuration.
        
        Args:
            config: Dictionary containing AWS SES configuration
        """
        if not AWS_SES_AVAILABLE:
            raise ImportError("AWS SDK not installed. Install with: pip install boto3")
        
        self.aws_access_key_id = config.get('aws_access_key_id')
        self.aws_secret_access_key = config.get('aws_secret_access_key')
        self.aws_region = config.get('aws_region', 'us-east-1')
        self.from_email = config.get('from_email', 'noreply@recruiterai.com')
        self.from_name = config.get('from_name', 'Recruiter AI')
        
        # Initialize SES client
        if self.aws_access_key_id and self.aws_secret_access_key:
            self.ses_client = boto3.client(
                'ses',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
        else:
            # Use default AWS credentials (IAM role, environment variables, etc.)
            self.ses_client = boto3.client('ses', region_name=self.aws_region)
    
    def get_provider_name(self) -> str:
        """Get the name of the email provider."""
        return "AWS SES"
    
    def validate_configuration(self) -> bool:
        """Validate that the provider is properly configured."""
        if not AWS_SES_AVAILABLE:
            logger.error("AWS SDK not installed")
            return False
        
        if not self.from_email:
            logger.error("AWS SES from_email is required")
            return False
        
        try:
            # Test SES connection
            self.ses_client.get_send_quota()
            return True
        except ClientError as e:
            logger.error(f"AWS SES configuration validation failed: {e}")
            return False
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """Send email using AWS SES."""
        try:
            # Use provided from_email/from_name or defaults
            sender_email = from_email or self.from_email
            sender_name = from_name or self.from_name
            
            # Prepare message
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {'Data': html_content, 'Charset': 'UTF-8'}
                }
            }
            
            # Add text content if provided
            if text_content:
                message['Body']['Text'] = {'Data': text_content, 'Charset': 'UTF-8'}
            
            # Send email
            response = self.ses_client.send_email(
                Source=f"{sender_name} <{sender_email}>",
                Destination={'ToAddresses': [to_email]},
                Message=message
            )
            
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                logger.info(f"Email sent successfully to {to_email} via AWS SES")
                return True
            else:
                logger.error(f"AWS SES error: {response}")
                return False
                
        except ClientError as e:
            logger.error(f"Failed to send email to {to_email} via AWS SES: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email via AWS SES: {e}")
            return False
