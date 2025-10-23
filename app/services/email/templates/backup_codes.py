# app/services/email/templates/backup_codes.py

from .base import EmailTemplate


class BackupCodesTemplate(EmailTemplate):
    """Template for backup codes emails."""

    def get_subject(self, **kwargs) -> str:
        """Get email subject."""
        return "Your Backup Codes for Recruiter AI"

    def get_html_content(self, **kwargs) -> str:
        """Get HTML email content."""
        backup_codes = kwargs.get('backup_codes', [])
        user_name = kwargs.get('user_name', 'User')
        
        # Format backup codes as a list
        codes_html = ""
        for i, code in enumerate(backup_codes, 1):
            codes_html += f"""
                <div style="background-color: #f8f9fa; padding: 8px 12px; margin: 4px 0; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 14px; font-weight: bold; color: #495057;">
                    {i}. {code}
                </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Backup Codes</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">🔐 Your Backup Codes</h1>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6;">
                <h2 style="color: #007bff; margin-top: 0;">Hello {user_name},</h2>
                
                <p>Your backup codes for Recruiter AI have been generated. These codes can be used to access your account when you cannot receive Email OTP codes.</p>
                
                <div style="background-color: #fff; padding: 20px; border-radius: 8px; border: 2px solid #28a745; margin: 20px 0;">
                    <h3 style="color: #28a745; margin-top: 0; text-align: center;">📋 Your Backup Codes</h3>
                    <div style="margin: 15px 0;">
                        {codes_html}
                    </div>
                </div>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #856404; margin-top: 0;">⚠️ Important Security Information:</h4>
                    <ul style="color: #856404; margin: 0; padding-left: 20px;">
                        <li><strong>Save these codes securely</strong> - Store them in a safe place</li>
                        <li><strong>Each code can only be used once</strong> - After use, it becomes invalid</li>
                        <li><strong>Never share these codes</strong> - They provide access to your account</li>
                        <li><strong>Generate new codes if needed</strong> - You can create new codes anytime</li>
                        <li><strong>Use when Email OTP fails</strong> - Enter any code during MFA verification</li>
                    </ul>
                </div>
                
                <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4 style="color: #0c5460; margin-top: 0;">💡 How to Use Backup Codes:</h4>
                    <ol style="color: #0c5460; margin: 0; padding-left: 20px;">
                        <li>When logging in, if Email OTP is not working</li>
                        <li>Enter any of the backup codes above instead of the Email OTP</li>
                        <li>The code will be consumed and cannot be used again</li>
                        <li>You can generate new codes anytime from your account settings</li>
                    </ol>
                </div>
                
                <p>If you didn't request these backup codes or have any concerns, please contact our support team immediately.</p>
                
                <div class="footer" style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; text-align: center; color: #6c757d; font-size: 14px;">
                    <p>This is an automated message from Recruiter AI. Please do not reply to this email.</p>
                    <p>© 2024 Recruiter AI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def get_text_content(self, **kwargs) -> str:
        """Get plain text email content."""
        backup_codes = kwargs.get('backup_codes', [])
        user_name = kwargs.get('user_name', 'User')
        
        # Format backup codes as a numbered list
        codes_text = ""
        for i, code in enumerate(backup_codes, 1):
            codes_text += f"{i}. {code}\n"
        
        return f"""
YOUR BACKUP CODES FOR RECRUITER AI

Hello {user_name},

Your backup codes for Recruiter AI have been generated. These codes can be used to access your account when you cannot receive Email OTP codes.

YOUR BACKUP CODES:
{codes_text}

IMPORTANT SECURITY INFORMATION:
- Save these codes securely - Store them in a safe place
- Each code can only be used once - After use, it becomes invalid
- Never share these codes - They provide access to your account
- Generate new codes if needed - You can create new codes anytime
- Use when Email OTP fails - Enter any code during MFA verification

HOW TO USE BACKUP CODES:
1. When logging in, if Email OTP is not working
2. Enter any of the backup codes above instead of the Email OTP
3. The code will be consumed and cannot be used again
4. You can generate new codes anytime from your account settings

If you didn't request these backup codes or have any concerns, please contact our support team immediately.

This is an automated message from Recruiter AI. Please do not reply to this email.

© 2024 Recruiter AI. All rights reserved.
        """
