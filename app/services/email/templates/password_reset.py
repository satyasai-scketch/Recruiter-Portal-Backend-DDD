"""
Password reset email template.
"""

from .base import EmailTemplate


class PasswordResetTemplate(EmailTemplate):
    """Template for password reset emails."""
    
    def get_subject(self, **kwargs) -> str:
        """Get the email subject."""
        return "Password Reset Request - Recruiter AI"
    
    def get_html_content(self, **kwargs) -> str:
        """Get the HTML email content."""
        user_name = kwargs.get('user_name', 'User')
        reset_url = kwargs.get('reset_url', '#')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Reset</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4f46e5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Recruiter AI</h1>
                </div>
                <div class="content">
                    <h2>Password Reset Request</h2>
                    <p>Hello {user_name},</p>
                    <p>We received a request to reset your password for your Recruiter AI account.</p>
                    <p>Click the button below to reset your password:</p>
                    <a href="{reset_url}" class="button">Reset Password</a>
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p><a href="{reset_url}">{reset_url}</a></p>
                    <p><strong>This link will expire in 1 hour for security reasons.</strong></p>
                    <p>If you didn't request this password reset, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This email was sent from Recruiter AI. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def get_text_content(self, **kwargs) -> str:
        """Get the plain text email content."""
        user_name = kwargs.get('user_name', 'User')
        reset_url = kwargs.get('reset_url', '#')
        
        return f"""
        Password Reset Request - Recruiter AI
        
        Hello {user_name},
        
        We received a request to reset your password for your Recruiter AI account.
        
        To reset your password, please visit the following link:
        {reset_url}
        
        This link will expire in 1 hour for security reasons.
        
        If you didn't request this password reset, please ignore this email.
        
        Best regards,
        Recruiter AI Team
        """
