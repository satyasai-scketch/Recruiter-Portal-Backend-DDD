# Email Service Architecture

This email service provides a flexible, provider-agnostic email system with template support.

## Architecture Overview

```
app/services/email/
├── __init__.py
├── email_service.py          # Main email service
├── providers/                # Email provider implementations
│   ├── __init__.py
│   ├── base.py              # Abstract provider interface
│   ├── smtp_provider.py     # SMTP implementation
│   ├── sendgrid_provider.py # SendGrid implementation
│   └── factory.py           # Provider factory
├── templates/               # Email templates
│   ├── __init__.py
│   ├── base.py             # Abstract template interface
│   ├── password_reset.py   # Password reset template
│   ├── welcome.py          # Welcome email template
│   └── factory.py          # Template factory
└── README.md               # This file
```

## Features

- **Provider Abstraction**: Easy switching between email providers
- **Template System**: Reusable email templates with HTML and text versions
- **Factory Pattern**: Easy provider and template creation
- **Configuration Management**: Environment-based configuration
- **Error Handling**: Comprehensive error handling and logging

## Supported Providers

### SMTP Provider
- Supports any SMTP server (Gmail, Outlook, custom servers)
- TLS/SSL support
- Authentication support

### SendGrid Provider
- SendGrid API integration
- Professional email delivery
- Analytics and tracking support

## Usage

### Basic Usage

```python
from app.services.email.email_service import email_service

# Send welcome email
email_service.send_welcome_email("user@example.com", "John Doe")

# Send password reset email
email_service.send_password_reset_email("user@example.com", "reset-token", "John Doe")
```

### Custom Email

```python
# Send custom email
email_service.send_custom_email(
    to_email="user@example.com",
    subject="Custom Subject",
    html_content="<h1>Hello World</h1>",
    text_content="Hello World"
)
```

### Template-based Email

```python
# Send email using template
email_service.send_template_email(
    template_name='welcome',
    to_email="user@example.com",
    user_name="John Doe"
)
```

## Configuration

### Environment Variables

```env
# Email Provider Selection
EMAIL_PROVIDER=smtp  # or 'sendgrid'

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# SendGrid Configuration
SENDGRID_API_KEY=your-sendgrid-api-key

# Common Settings
FROM_EMAIL=noreply@recruiterai.com
FROM_NAME=Recruiter AI
FRONTEND_URL=http://localhost:3000
```

## Adding New Providers

1. Create a new provider class in `providers/` directory
2. Implement the `EmailProvider` interface
3. Register the provider in `providers/factory.py`

```python
# Example: New provider
class NewProvider(EmailProvider):
    def send_email(self, to_email, subject, html_content, text_content=None, from_email=None, from_name=None):
        # Implementation
        pass
    
    def validate_configuration(self):
        # Validation logic
        pass
    
    def get_provider_name(self):
        return "NewProvider"

# Register in factory
EmailProviderFactory.register_provider('new_provider', NewProvider)
```

## Adding New Templates

1. Create a new template class in `templates/` directory
2. Implement the `EmailTemplate` interface
3. Register the template in `templates/factory.py`

```python
# Example: New template
class NewTemplate(EmailTemplate):
    def get_subject(self, **kwargs):
        return "New Email Subject"
    
    def get_html_content(self, **kwargs):
        return "<h1>HTML Content</h1>"
    
    def get_text_content(self, **kwargs):
        return "Text Content"

# Register in factory
EmailTemplateFactory.register_template('new_template', NewTemplate)
```

## Migration Between Providers

To switch from SMTP to SendGrid:

1. Update environment variables:
```env
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-api-key
```

2. No code changes required - the service automatically uses the new provider

## Error Handling

The service includes comprehensive error handling:
- Provider validation
- Configuration validation
- Email sending failures
- Template rendering errors

All errors are logged with appropriate detail levels.

## Testing

Each provider and template can be tested independently:

```python
# Test provider
provider = EmailProviderFactory.create_provider('smtp', config)
assert provider.validate_configuration()

# Test template
template = EmailTemplateFactory.create_template('welcome')
subject = template.get_subject(user_name="Test User")
```

## Best Practices

1. **Use Templates**: Prefer templates over custom HTML for consistency
2. **Validate Configuration**: Always validate provider configuration before sending
3. **Handle Errors**: Implement proper error handling for email failures
4. **Logging**: Use appropriate logging levels for debugging
5. **Environment Variables**: Use environment variables for sensitive configuration
