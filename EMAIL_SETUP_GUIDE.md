# Email Setup Guide

This guide helps you configure email providers for the Recruiter AI application.

## Gmail SMTP Setup

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. Enable 2-Step Verification if not already enabled

### Step 2: Generate App Password
1. Go to Google Account settings
2. Navigate to Security → 2-Step Verification
3. Scroll down to "App passwords"
4. Click "App passwords"
5. Select "Mail" and your device
6. Copy the generated 16-character password

### Step 3: Configure Environment Variables
Create a `.env` file in your project root:

```env
# Email Configuration
EMAIL_PROVIDER=smtp

# SMTP Configuration (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-character-app-password
SMTP_USE_TLS=true

# Common Email Settings
FROM_EMAIL=your-email@gmail.com
FROM_NAME=Recruiter AI
FRONTEND_URL=http://localhost:3000
```

### Step 4: Test Configuration
The application will automatically validate the email configuration on startup.

## SendGrid Setup

### Step 1: Create SendGrid Account
1. Go to [SendGrid](https://sendgrid.com/)
2. Create a free account
3. Verify your sender identity

### Step 2: Generate API Key
1. Go to Settings → API Keys
2. Create a new API key
3. Give it "Full Access" permissions
4. Copy the API key

### Step 3: Configure Environment Variables
```env
# Email Configuration
EMAIL_PROVIDER=sendgrid

# SendGrid Configuration
SENDGRID_API_KEY=your-sendgrid-api-key

# Common Email Settings
FROM_EMAIL=your-verified-email@domain.com
FROM_NAME=Recruiter AI
FRONTEND_URL=http://localhost:3000
```

## AWS SES Setup

### Step 1: Create AWS Account
1. Go to [AWS Console](https://aws.amazon.com/)
2. Navigate to Amazon SES
3. Verify your email address or domain

### Step 2: Create IAM User
1. Go to IAM → Users
2. Create a new user with SES permissions
3. Generate access keys

### Step 3: Configure Environment Variables
```env
# Email Configuration
EMAIL_PROVIDER=aws_ses

# AWS SES Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1

# Common Email Settings
FROM_EMAIL=your-verified-email@domain.com
FROM_NAME=Recruiter AI
FRONTEND_URL=http://localhost:3000
```

## Troubleshooting

### Gmail Authentication Issues
- **Error 535**: Username and Password not accepted
  - Make sure you're using an App Password, not your regular password
  - Ensure 2-Factor Authentication is enabled
  - Check that the email address is correct

### SendGrid Issues
- **Error 401**: Unauthorized
  - Verify your API key is correct
  - Ensure the sender email is verified in SendGrid

### AWS SES Issues
- **Error 403**: Access Denied
  - Check your IAM permissions
  - Ensure the sender email is verified in SES

## Development Mode

For development, you can use a mock email service by setting:

```env
EMAIL_PROVIDER=smtp
SMTP_SERVER=localhost
SMTP_PORT=1025
# Leave username and password empty for local testing
```

This will attempt to connect to a local SMTP server (like MailHog) for testing.

## Security Notes

- Never commit email credentials to version control
- Use environment variables for all sensitive configuration
- Regularly rotate API keys and passwords
- Use App Passwords instead of main passwords for Gmail
