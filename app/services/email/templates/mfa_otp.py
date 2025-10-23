"""
Email template for MFA OTP (One-Time Password) emails.
"""

from .base import EmailTemplate


class MFAOTPTemplate(EmailTemplate):
    """Template for MFA OTP emails."""
    
    def get_subject(self, **kwargs) -> str:
        """Get email subject."""
        return "Recruiter AI - Login Verification Code"
    
    def get_html_content(self, **kwargs) -> str:
        """Get HTML email content."""
        otp_code = kwargs.get('otp_code', '')
        user_name = kwargs.get('user_name', 'User')
        expiry_minutes = kwargs.get('expiry_minutes', 10)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>MFA Code</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .otp-code {{
                    background-color: #e9ecef;
                    border: 2px solid #dee2e6;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 4px;
                    color: #495057;
                    margin: 20px 0;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 4px;
                    padding: 15px;
                    margin: 20px 0;
                    color: #856404;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #dee2e6;
                    font-size: 14px;
                    color: #6c757d;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Recruiter AI - Login Verification</h1>
            </div>
            
            <p>Hello {user_name},</p>
            
            <p>You have requested to access your Recruiter AI account. Please use the following verification code to complete your login:</p>
            
            <div class="otp-code">
                {otp_code}
            </div>
            
            <div class="warning">
                <strong>⚠️ Important Security Information:</strong>
                <ul>
                    <li>This code will expire in {expiry_minutes} minutes</li>
                    <li>Never share this code with anyone</li>
                    <li>If you didn't request this code, please ignore this email</li>
                    <li>For security, this code can only be used once</li>
                </ul>
            </div>
            
            <p>If you're having trouble logging in, please contact our support team.</p>
            
            <div class="footer">
                <p>This is an automated message from Recruiter AI. Please do not reply to this email.</p>
                <p>© 2024 Recruiter AI. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
    
    def get_text_content(self, **kwargs) -> str:
        """Get plain text email content."""
        otp_code = kwargs.get('otp_code', '')
        user_name = kwargs.get('user_name', 'User')
        expiry_minutes = kwargs.get('expiry_minutes', 10)
        
        return f"""
RECRUITER AI - LOGIN VERIFICATION CODE

Hello {user_name},

You have requested to access your Recruiter AI account. Please use the following verification code to complete your login:

{otp_code}

IMPORTANT SECURITY INFORMATION:
- This code will expire in {expiry_minutes} minutes
- Never share this code with anyone
- If you didn't request this code, please ignore this email
- For security, this code can only be used once

If you're having trouble logging in, please contact our support team.

This is an automated message from Recruiter AI. Please do not reply to this email.

© 2024 Recruiter AI. All rights reserved.
        """
