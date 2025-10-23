# System-Level MFA Configuration Guide

## Overview

This document provides a comprehensive guide to the updated Multi-Factor Authentication (MFA) implementation in the Recruiter AI Backend. The system now uses **system-level configuration** where MFA is enabled or disabled for all users based on a single system setting, and currently supports **Email OTP only** as the authentication method.

## Key Changes

### 1. System-Level Configuration
- **Global Control**: MFA is controlled by a single system setting (`MFA_ENABLED`)
- **All or Nothing**: When enabled, MFA is available to all users; when disabled, no users can use MFA
- **Centralized Management**: Administrators control MFA for the entire system

### 2. Email OTP Only
- **Single Method**: Only Email OTP is currently available to users
- **TOTP Preserved**: TOTP functionality is kept in the codebase for future use but not exposed in the API
- **Simplified UX**: Users have one clear authentication method

## Configuration

### Environment Variables
```python
# System-Level MFA Configuration
MFA_ENABLED=true                    # Master switch for all MFA functionality
MFA_EMAIL_OTP_ENABLED=true          # Email OTP specific setting
MFA_EMAIL_OTP_LENGTH=6              # OTP code length (default: 6)
MFA_EMAIL_OTP_EXPIRY_MINUTES=10     # Code expiry time (default: 10 minutes)
MFA_EMAIL_OTP_MAX_ATTEMPTS=3        # Max verification attempts (default: 3)

# Legacy TOTP settings (preserved for future use)
MFA_ISSUER_NAME="Recruiter AI"
MFA_TOTP_WINDOW=1
MFA_BACKUP_CODES_COUNT=10
MFA_BACKUP_CODE_LENGTH=8
MFA_MAX_LOGIN_ATTEMPTS=5
MFA_LOCKOUT_DURATION_MINUTES=15
MFA_REQUIRE_BACKUP_CODES=true
```

## System Behavior

### When MFA is Disabled (`MFA_ENABLED=false`)
- **No MFA Required**: All users can login with just email/password
- **No MFA Endpoints**: MFA-related endpoints return appropriate error messages
- **No MFA Setup**: Users cannot enable MFA even if they want to
- **Status Response**: MFA status shows `system_enabled: false`

### When MFA is Enabled (`MFA_ENABLED=true`)
- **MFA Available**: Users can enable Email OTP for their accounts
- **Optional for Users**: Individual users can choose to enable/disable Email OTP
- **Login Flow**: Users with MFA enabled must complete Email OTP verification
- **Status Response**: MFA status shows `system_enabled: true`

## API Endpoints

### Available Endpoints (Email OTP Only)
1. **GET /api/v1/mfa/status** - Get MFA status (includes system-level info)
2. **POST /api/v1/mfa/email-otp/enable** - Enable Email OTP for user
3. **POST /api/v1/mfa/email-otp/disable** - Disable Email OTP for user
4. **POST /api/v1/mfa/email-otp/send** - Send Email OTP code
5. **POST /api/v1/mfa/email-otp/verify** - Verify Email OTP code

### Removed Endpoints (TOTP)
- ~~POST /api/v1/mfa/setup~~ - TOTP setup (removed from API)
- ~~POST /api/v1/mfa/verify~~ - TOTP verification (removed from API)
- ~~POST /api/v1/mfa/disable~~ - General MFA disable (removed from API)
- ~~POST /api/v1/mfa/regenerate-backup-codes~~ - Backup codes (removed from API)

### Authentication Endpoints
- **POST /api/v1/auth/login** - Initial login (returns MFA token if needed)
- **POST /api/v1/auth/login/mfa** - Complete MFA verification

## Usage Examples

### 1. Check System MFA Status

```bash
curl -X GET "http://localhost:8000/api/v1/mfa/status" \
  -H "Authorization: Bearer <access_token>"
```

**Response when MFA is enabled:**
```json
{
  "enabled": false,
  "system_enabled": true,
  "email_otp_enabled": false,
  "email_otp_verified": false,
  "backup_codes_generated": false,
  "backup_codes_remaining": 0
}
```

**Response when MFA is disabled:**
```json
{
  "enabled": false,
  "system_enabled": false,
  "email_otp_enabled": false,
  "email_otp_verified": false,
  "backup_codes_generated": false,
  "backup_codes_remaining": 0
}
```

### 2. Enable Email OTP (when system MFA is enabled)

```bash
curl -X POST "http://localhost:8000/api/v1/mfa/email-otp/enable" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
```json
{
  "success": true,
  "message": "Email OTP has been successfully enabled"
}
```

### 3. Login Flow with Email OTP

#### Step 1: Initial Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

**Response (if MFA enabled for user):**
```json
{
  "access_token": null,
  "token_type": "bearer",
  "user": {...},
  "mfa_required": true,
  "mfa_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Step 2: Send Email OTP
```bash
curl -X POST "http://localhost:8000/api/v1/mfa/email-otp/send" \
  -H "Authorization: Bearer <mfa_token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### Step 3: Complete MFA Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/mfa" \
  -H "Content-Type: application/json" \
  -d '{"mfa_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", "mfa_code": "123456"}'
```

## Error Handling

### System-Level Errors
```json
{
  "detail": "MFA is not enabled system-wide"
}
```

### User-Level Errors
```json
{
  "detail": "Email OTP is not enabled for this user"
}
```

### Configuration Errors
```json
{
  "detail": "Email OTP is not enabled"
}
```

## Frontend Integration

### 1. Check System MFA Status
```javascript
const checkMFAStatus = async () => {
  const response = await fetch('/api/v1/mfa/status', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const status = await response.json();
  
  if (!status.system_enabled) {
    // Show message: "MFA is not available"
    return;
  }
  
  if (!status.enabled) {
    // Show "Enable MFA" button
  } else {
    // Show MFA management options
  }
};
```

### 2. Enable Email OTP
```javascript
const enableEmailOTP = async () => {
  const response = await fetch('/api/v1/mfa/email-otp/enable', {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({})
  });
  
  const result = await response.json();
  if (result.success) {
    // Show success message
  }
};
```

### 3. Login with Email OTP
```javascript
const loginWithMFA = async (email, password) => {
  // Step 1: Initial login
  const loginResponse = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const loginData = await loginResponse.json();
  
  if (loginData.mfa_required) {
    // Step 2: Send Email OTP
    await fetch('/api/v1/mfa/email-otp/send', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${loginData.mfa_token}` }
    });
    
    // Step 3: Get OTP from user and complete login
    const otpCode = prompt('Enter the 6-digit code from your email:');
    
    const mfaResponse = await fetch('/api/v1/auth/login/mfa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mfa_token: loginData.mfa_token,
        mfa_code: otpCode
      })
    });
    
    const finalResult = await mfaResponse.json();
    return finalResult.access_token;
  }
  
  return loginData.access_token;
};
```

## Administration

### Enabling MFA System-Wide
1. Set `MFA_ENABLED=true` in environment variables
2. Restart the application
3. All users can now enable Email OTP

### Disabling MFA System-Wide
1. Set `MFA_ENABLED=false` in environment variables
2. Restart the application
3. All MFA functionality is disabled

### Monitoring MFA Usage
- Check MFA status endpoint for system-wide status
- Monitor email delivery for OTP codes
- Review login attempts and MFA verification logs

## Security Considerations

### System-Level Security
- **Centralized Control**: MFA can be disabled instantly across the entire system
- **Emergency Access**: Administrators can disable MFA if needed for system recovery
- **Consistent Policy**: All users follow the same MFA policy

### User-Level Security
- **Optional for Users**: Users can choose to enable/disable Email OTP
- **Secure by Default**: When MFA is system-enabled, users must explicitly enable it
- **Audit Trail**: All MFA activities are logged

## Migration from Previous Version

### For Existing Users
- Users with TOTP enabled will need to switch to Email OTP
- Backup codes are preserved but not exposed in the API
- TOTP secrets are kept in the database for future use

### For Administrators
- Update environment variables to use system-level configuration
- Remove TOTP-related UI components
- Update frontend to use Email OTP only

## Future Enhancements

### Planned Features
1. **TOTP Re-enablement**: Add TOTP back to the API when needed
2. **SMS OTP**: Add SMS-based OTP as another option
3. **Admin Panel**: Web interface for system-level MFA management
4. **User Groups**: Different MFA policies for different user groups

### Configuration Options
1. **Per-Role MFA**: Different MFA requirements for different roles
2. **Grace Period**: Temporary MFA bypass for new users
3. **Device Trust**: Remember trusted devices
4. **Risk-Based**: Dynamic MFA based on risk factors

## Troubleshooting

### Common Issues

1. **MFA Not Working**
   - Check `MFA_ENABLED` setting
   - Verify email service configuration
   - Check user's Email OTP status

2. **Email OTP Not Received**
   - Verify email provider settings
   - Check spam/junk folders
   - Ensure email service is working

3. **System-Level Errors**
   - Verify environment variable configuration
   - Check application logs
   - Restart application after configuration changes

### Debug Information
- Check `/api/v1/mfa/status` for current configuration
- Review application logs for MFA-related errors
- Verify email service configuration and delivery

## Support

For technical support:
- Check system MFA status via API
- Review application logs for detailed error information
- Verify email service configuration
- Contact development team with specific error messages and timestamps

The system-level MFA configuration provides centralized control while maintaining security and flexibility for individual users.
