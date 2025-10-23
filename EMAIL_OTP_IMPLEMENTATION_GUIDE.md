# Email OTP Implementation Guide

## Overview

This document provides a comprehensive guide to the Email OTP (One-Time Password) implementation as an additional Multi-Factor Authentication method in the Recruiter AI Backend. Email OTP provides users with an alternative to TOTP-based authentication, offering convenience and accessibility.

## Features Implemented

### 1. Email OTP Generation and Delivery
- **Code Length**: 6 digits (configurable)
- **Expiry Time**: 10 minutes (configurable)
- **Max Attempts**: 3 verification attempts (configurable)
- **Secure Storage**: SHA-256 hashed codes
- **Email Template**: Professional HTML and text templates

### 2. Security Features
- **Rate Limiting**: Maximum 3 verification attempts per OTP
- **Expiry Management**: Automatic code expiration
- **Single Use**: Codes are marked as used after successful verification
- **Secure Hashing**: All OTP codes are hashed before storage
- **Audit Logging**: Complete activity tracking

### 3. Integration with Existing MFA
- **Multiple Methods**: Users can enable both TOTP and Email OTP
- **Unified Login**: Single login flow supports both methods
- **Status Management**: Independent enable/disable for each method
- **Backup Codes**: Shared backup codes work with both methods

## Architecture

### Database Models

#### 1. Updated MFAModel (`user_mfa` table)
```sql
- email_otp_enabled: Boolean flag for Email OTP status
- email_otp_verified: Boolean flag for Email OTP verification
```

#### 2. New MFAEmailOTPModel (`mfa_email_otp` table)
```sql
- id: Primary key
- user_id: Foreign key to users table
- otp_code: SHA-256 hash of the OTP code
- expires_at: Expiration timestamp
- used: Boolean flag for usage status
- attempts: Number of verification attempts
- created_at: Creation timestamp
```

### Service Layer

#### MFAService Extensions
New methods added to the existing MFAService:

- **`generate_email_otp()`**: Generate random numeric OTP codes
- **`send_email_otp()`**: Send OTP via email with proper error handling
- **`verify_email_otp()`**: Verify OTP codes with attempt tracking
- **`enable_email_otp()`**: Enable Email OTP for a user
- **`disable_email_otp()`**: Disable Email OTP and clean up codes
- **Updated `verify_mfa_login()`**: Support for Email OTP verification
- **Updated `get_mfa_status()`**: Include Email OTP status

### Email Integration

#### Email Template
- **Professional Design**: Clean, responsive HTML template
- **Security Warnings**: Clear instructions about code security
- **Expiry Information**: Prominent display of code expiration
- **Branding**: Consistent with application branding

#### Email Service Integration
- **Template System**: Integrated with existing email template system
- **Provider Support**: Works with all configured email providers (SMTP, SendGrid, AWS SES)
- **Error Handling**: Comprehensive error handling and cleanup

## API Endpoints

### Email OTP Management
1. **POST /api/v1/mfa/email-otp/enable** - Enable Email OTP
2. **POST /api/v1/mfa/email-otp/disable** - Disable Email OTP
3. **POST /api/v1/mfa/email-otp/send** - Send Email OTP
4. **POST /api/v1/mfa/email-otp/verify** - Verify Email OTP

### Updated Endpoints
1. **GET /api/v1/mfa/status** - Now includes Email OTP status
2. **POST /api/v1/auth/login/mfa** - Supports Email OTP verification

## Configuration

### Environment Variables
```python
# Email OTP Configuration
MFA_EMAIL_OTP_ENABLED=true
MFA_EMAIL_OTP_LENGTH=6
MFA_EMAIL_OTP_EXPIRY_MINUTES=10
MFA_EMAIL_OTP_MAX_ATTEMPTS=3
```

## Usage Examples

### 1. Enabling Email OTP

```bash
curl -X POST "http://localhost:8000/api/v1/mfa/email-otp/enable" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Response:
```json
{
  "success": true,
  "message": "Email OTP has been successfully enabled"
}
```

### 2. Sending Email OTP

```bash
curl -X POST "http://localhost:8000/api/v1/mfa/email-otp/send" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Response:
```json
{
  "success": true,
  "message": "Email OTP has been sent successfully"
}
```

### 3. Verifying Email OTP

```bash
curl -X POST "http://localhost:8000/api/v1/mfa/email-otp/verify" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"otp_code": "123456"}'
```

### 4. Login with Email OTP

```bash
# Step 1: Initial login (same as before)
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Step 2: Complete MFA with Email OTP
curl -X POST "http://localhost:8000/api/v1/auth/login/mfa" \
  -H "Content-Type: application/json" \
  -d '{"mfa_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", "mfa_code": "123456"}'
```

### 5. Checking MFA Status

```bash
curl -X GET "http://localhost:8000/api/v1/mfa/status" \
  -H "Authorization: Bearer <access_token>"
```

Response:
```json
{
  "enabled": true,
  "totp_enabled": false,
  "totp_verified": false,
  "email_otp_enabled": true,
  "email_otp_verified": true,
  "backup_codes_generated": true,
  "backup_codes_remaining": 8
}
```

## Security Considerations

### 1. Code Generation
- **Cryptographically Secure**: Uses `secrets` module for random generation
- **Numeric Only**: 6-digit numeric codes for easy entry
- **No Patterns**: Completely random with no predictable sequences

### 2. Storage Security
- **Hashed Storage**: All OTP codes are SHA-256 hashed before storage
- **No Plaintext**: Never store plaintext OTP codes in database
- **Automatic Cleanup**: Expired and used codes are automatically cleaned up

### 3. Rate Limiting
- **Attempt Limiting**: Maximum 3 verification attempts per OTP
- **Expiry Management**: Codes expire after 10 minutes
- **Lockout Protection**: Failed attempts are tracked and limited

### 4. Email Security
- **Professional Templates**: Clear security warnings in emails
- **No Sensitive Data**: Only OTP codes are sent via email
- **Delivery Confirmation**: Email delivery is verified before code activation

## Frontend Integration

### 1. Email OTP Setup
```javascript
// Enable Email OTP
const enableResponse = await fetch('/api/v1/mfa/email-otp/enable', {
  method: 'POST',
  headers: { 
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json' 
  },
  body: JSON.stringify({})
});
```

### 2. Send Email OTP
```javascript
// Send OTP to user's email
const sendResponse = await fetch('/api/v1/mfa/email-otp/send', {
  method: 'POST',
  headers: { 
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json' 
  },
  body: JSON.stringify({})
});
```

### 3. Verify Email OTP
```javascript
// Verify OTP code
const verifyResponse = await fetch('/api/v1/mfa/email-otp/verify', {
  method: 'POST',
  headers: { 
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json' 
  },
  body: JSON.stringify({
    otp_code: document.getElementById('otp-code').value
  })
});
```

### 4. Login Flow with Email OTP
```javascript
// Step 1: Initial login
const loginResponse = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const loginData = await loginResponse.json();

if (loginData.mfa_required) {
  // Step 2: Send Email OTP (if Email OTP is enabled)
  if (userHasEmailOTP) {
    await fetch('/api/v1/mfa/email-otp/send', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${mfaToken}` }
    });
  }
  
  // Step 3: Complete MFA verification
  const mfaResponse = await fetch('/api/v1/auth/login/mfa', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      mfa_token: loginData.mfa_token,
      mfa_code: otpCode
    })
  });
}
```

## Testing

### 1. Unit Tests
```python
def test_email_otp_generation():
    mfa_service = MFAService()
    otp = mfa_service.generate_email_otp()
    assert len(otp) == 6
    assert otp.isdigit()

def test_email_otp_verification():
    mfa_service = MFAService()
    otp = mfa_service.generate_email_otp()
    otp_hash = hashlib.sha256(otp.encode()).hexdigest()
    assert mfa_service.verify_email_otp(db, user_id, otp)
```

### 2. Integration Tests
```python
def test_email_otp_login_flow():
    # Enable Email OTP
    # Send OTP
    # Verify OTP
    # Complete login
```

### 3. Email Testing
- Test with different email providers
- Verify email delivery
- Test email template rendering
- Test error handling for email failures

## Monitoring and Logging

### 1. Email OTP Events
- OTP generation and sending
- Verification attempts (success/failure)
- Code expiry and cleanup
- Email delivery status

### 2. Security Monitoring
- Multiple failed verification attempts
- Unusual OTP request patterns
- Email delivery failures
- Rate limiting triggers

## Troubleshooting

### Common Issues

1. **Email Not Received**
   - Check email provider configuration
   - Verify email address is correct
   - Check spam/junk folders
   - Verify email service is working

2. **OTP Code Not Working**
   - Check if code has expired (10 minutes)
   - Verify code was entered correctly
   - Check if maximum attempts exceeded (3)
   - Ensure code hasn't been used already

3. **Email OTP Not Enabled**
   - Verify Email OTP is enabled in settings
   - Check if user has Email OTP enabled
   - Ensure email service is configured

### Debug Information
- Check MFA status endpoint for current configuration
- Review email service logs for delivery issues
- Monitor database for OTP records and expiry

## Performance Considerations

### 1. Database Optimization
- Indexes on user_id, expires_at, and used columns
- Automatic cleanup of expired codes
- Efficient query patterns for verification

### 2. Email Performance
- Asynchronous email sending (if supported by provider)
- Email template caching
- Rate limiting to prevent abuse

### 3. Security Performance
- Efficient hashing algorithms
- Minimal database queries
- Optimized verification logic

## Future Enhancements

### Planned Features
1. **SMS OTP**: SMS-based OTP delivery
2. **Push Notifications**: Mobile app push notifications
3. **Voice OTP**: Phone call-based OTP delivery
4. **Custom Expiry**: User-configurable OTP expiry times
5. **OTP History**: Track OTP usage history

### Advanced Security
1. **Device Fingerprinting**: Associate OTPs with specific devices
2. **Geolocation Verification**: Location-based OTP validation
3. **Behavioral Analysis**: Detect unusual OTP request patterns
4. **Risk Scoring**: Dynamic OTP requirements based on risk

## Compliance

This implementation follows:
- **NIST SP 800-63B**: Digital Identity Guidelines
- **OWASP**: Authentication security guidelines
- **GDPR**: Data protection requirements
- **SOC 2**: Security controls
- **Email Security**: Best practices for email-based authentication

## Support

For technical support or security concerns:
- Check application logs for detailed error information
- Verify email service configuration
- Review MFA status and settings
- Contact development team with specific error messages and timestamps

The Email OTP implementation provides a secure, user-friendly alternative to TOTP-based authentication while maintaining the same high security standards and audit capabilities.
