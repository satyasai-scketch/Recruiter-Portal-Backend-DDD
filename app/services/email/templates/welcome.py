"""
Welcome email template.
"""

from .base import EmailTemplate


class WelcomeTemplate(EmailTemplate):
    """Template for welcome emails."""
    
    def get_subject(self, **kwargs) -> str:
        """Get the email subject."""
        return "Welcome to Recruiter AI!"
    
    def get_html_content(self, **kwargs) -> str:
        """Get the HTML email content."""
        user_name = kwargs.get('user_name', 'User')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Recruiter AI</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4f46e5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9fafb; }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
                ul {{ padding-left: 20px; }}
                li {{ margin-bottom: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Recruiter AI!</h1>
                </div>
                <div class="content">
                    <h2>Hello {user_name}!</h2>
                    <p>Welcome to Recruiter AI! Your account has been successfully created.</p>
                    <p>You can now start using our platform to:</p>
                    <ul>
                        <li>Create and refine job descriptions</li>
                        <li>Generate AI-powered personas</li>
                        <li>Upload and analyze candidate CVs</li>
                        <li>Get intelligent candidate recommendations</li>
                    </ul>
                    <p>If you have any questions, feel free to contact our support team.</p>
                </div>
                <div class="footer">
                    <p>Thank you for choosing Recruiter AI!</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def get_text_content(self, **kwargs) -> str:
        """Get the plain text email content."""
        user_name = kwargs.get('user_name', 'User')
        
        return f"""
        Welcome to Recruiter AI!
        
        Hello {user_name}!
        
        Welcome to Recruiter AI! Your account has been successfully created.
        
        You can now start using our platform to:
        - Create and refine job descriptions
        - Generate AI-powered personas
        - Upload and analyze candidate CVs
        - Get intelligent candidate recommendations
        
        If you have any questions, feel free to contact our support team.
        
        Thank you for choosing Recruiter AI!
        """
