# Mandatory MFA Configuration Guide

## Overview

This document provides a comprehensive guide to the **Mandatory Multi-Factor Authentication (MFA)** implementation in the Recruiter AI Backend. The system now enforces **mandatory MFA** for all users when system-level MFA is enabled, with users having the option to disable it if they choose.

## Key Features

### 1. **Mandatory MFA by Default**
- **System-Level Control**: When `MFA_ENABLED=true`, MFA becomes mandatory for all users
- **Auto-Enable**: New users automatically have MFA enabled during signup
- **Existing Users**: Existing users without MFA must set it up before they can login
- **Optional Disable**: Users can choose to disable MFA, but it's enabled by default

### 2. **Email OTP Only**
- **Single Method**: Only Email OTP is currently available
- **Automatic Setup**: Email OTP is automatically enabled for new users
- **User Choice**: Users can disable Email OTP if they prefer

## System Behavior

### **When MFA is Disabled (`MFA_ENABLED=false`)**
- **No MFA Required**: All users can login with just email/password
- **No Auto-Enable**: New users don't get MFA enabled automatically
- **No MFA Endpoints**: MFA-related endpoints return appropriate error messages
- **Status Response**: MFA status shows `system_enabled: false`

### **When MFA is Enabled (`MFA_ENABLED=true`)**
- **Mandatory for All**: All users must have MFA enabled to login
- **Auto-Enable New Users**: New users automatically get MFA enabled during signup
- **Existing Users**: Must set up MFA before they can login
- **Optional Disable**: Users can disable MFA if they choose, but it's enabled by default
- **Login Flow**: All users must complete MFA verification to login

## User Experience Flow

### **New User Signup**
1. User creates account with email/password
2. **System automatically enables MFA** (Email OTP)
3. User receives welcome email
4. User can login immediately (MFA is already set up)

### **Existing User Login (First Time After MFA Enable)**
1. User tries to login with email/password
2. System returns MFA token (MFA required)
3. **User must set up MFA first** (if not already set up)
4. User calls `/api/v1/mfa/setup` to enable MFA
5. User can then proceed with normal MFA login flow

### **Normal Login Flow**
1. User submits email/password
2. System returns MFA token (MFA required)
3. User requests Email OTP via `/api/v1/mfa/email-otp/send`
4. User enters OTP code from email
5. System returns final access token

## API Endpoints

### **MFA Management**
1. **GET /api/v1/mfa/status** - Get MFA status (includes setup_required flag)
2. **POST /api/v1/mfa/setup** - Setup MFA for user (mandatory for existing users)
3. **POST /api/v1/mfa/email-otp/enable** - Enable Email OTP
4. **POST /api/v1/mfa/email-otp/disable** - Disable Email OTP (user choice)
5. **POST /api/v1/mfa/email-otp/send** - Send Email OTP code
6. **POST /api/v1/mfa/email-otp/verify** - Verify Email OTP code

### **Authentication**
- **POST /api/v1/auth/login** - Initial login (returns MFA token if MFA required)
- **POST /api/v1/auth/login/mfa** - Complete MFA verification

## Configuration

### **Environment Variables**
```env
# System-Level MFA Configuration
MFA_ENABLED=true                    # Master switch - when true, MFA is mandatory for all users
MFA_EMAIL_OTP_ENABLED=true          # Email OTP specific setting
MFA_EMAIL_OTP_LENGTH=6              # OTP code length
MFA_EMAIL_OTP_EXPIRY_MINUTES=10     # Code expiry time
MFA_EMAIL_OTP_MAX_ATTEMPTS=3        # Max verification attempts
```

## Usage Examples

### **1. Check MFA Status**

```bash
curl -X GET "http://localhost:8000/api/v1/mfa/status" \
  -H "Authorization: Bearer <access_token>"
```

**Response for new user (MFA auto-enabled):**
```json
{
  "enabled": true,
  "system_enabled": true,
  "email_otp_enabled": true,
  "email_otp_verified": true,
  "backup_codes_generated": false,
  "backup_codes_remaining": 0,
  "setup_required": false
}
```

**Response for existing user (needs setup):**
```json
{
  "enabled": false,
  "system_enabled": true,
  "email_otp_enabled": false,
  "email_otp_verified": false,
  "backup_codes_generated": false,
  "backup_codes_remaining": 0,
  "setup_required": true
}
```

### **2. Setup MFA (for existing users)**

```bash
curl -X POST "http://localhost:8000/api/v1/mfa/setup" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
```json
{
  "success": true,
  "message": "MFA has been successfully set up and enabled"
}
```

### **3. Login Flow for Existing User (First Time)**

#### Step 1: Initial Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

**Response:**
```json
{
  "access_token": null,
  "token_type": "bearer",
  "user": {...},
  "mfa_required": true,
  "mfa_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Step 2: Setup MFA (if not already set up)
```bash
curl -X POST "http://localhost:8000/api/v1/mfa/setup" \
  -H "Authorization: Bearer <mfa_token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### Step 3: Send Email OTP
```bash
curl -X POST "http://localhost:8000/api/v1/mfa/email-otp/send" \
  -H "Authorization: Bearer <mfa_token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### Step 4: Complete MFA Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/mfa" \
  -H "Content-Type: application/json" \
  -d '{"mfa_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", "mfa_code": "123456"}'
```

### **4. User Disables MFA (Optional)**

```bash
curl -X POST "http://localhost:8000/api/v1/mfa/email-otp/disable" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"password": "user_password"}'
```

**Response:**
```json
{
  "success": true,
  "message": "Email OTP has been successfully disabled"
}
```

## Error Handling

### **MFA Setup Required**
```json
{
  "detail": "MFA setup required. Please enable Email OTP first."
}
```

### **MFA Mandatory**
```json
{
  "detail": "Email OTP not enabled for this user. MFA is mandatory when system MFA is enabled."
}
```

### **System MFA Disabled**
```json
{
  "detail": "MFA is not enabled system-wide"
}
```

## Frontend Integration

### **1. Check MFA Status and Handle Setup**

```javascript
const checkAndSetupMFA = async () => {
  const response = await fetch('/api/v1/mfa/status', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const status = await response.json();
  
  if (!status.system_enabled) {
    // Show message: "MFA is not available"
    return;
  }
  
  if (status.setup_required) {
    // Show MFA setup screen
    await setupMFA();
  } else if (!status.enabled) {
    // Show "Enable MFA" button (optional)
  } else {
    // Show MFA management options
  }
};

const setupMFA = async () => {
  const response = await fetch('/api/v1/mfa/setup', {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({})
  });
  
  const result = await response.json();
  if (result.success) {
    // Show success message and proceed
  }
};
```

### **2. Login Flow with Mandatory MFA**

```javascript
const loginWithMandatoryMFA = async (email, password) => {
  // Step 1: Initial login
  const loginResponse = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const loginData = await loginResponse.json();
  
  if (loginData.mfa_required) {
    // Step 2: Check if MFA setup is required
    const statusResponse = await fetch('/api/v1/mfa/status', {
      headers: { 'Authorization': `Bearer ${loginData.mfa_token}` }
    });
    const status = await statusResponse.json();
    
    if (status.setup_required) {
      // Step 3: Setup MFA first
      await fetch('/api/v1/mfa/setup', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${loginData.mfa_token}` }
      });
    }
    
    // Step 4: Send Email OTP
    await fetch('/api/v1/mfa/email-otp/send', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${loginData.mfa_token}` }
    });
    
    // Step 5: Get OTP from user and complete login
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

## Security Considerations

### **Mandatory MFA Benefits**
- **Enhanced Security**: All users have MFA enabled by default
- **Consistent Policy**: No users can bypass MFA when system MFA is enabled
- **Automatic Protection**: New users are automatically protected
- **Emergency Control**: Administrators can disable MFA system-wide if needed

### **User Choice**
- **Optional Disable**: Users can disable MFA if they prefer
- **Re-enable**: Users can re-enable MFA at any time
- **No Forced Setup**: Users aren't forced to set up MFA during signup (it's automatic)

### **System Control**
- **Centralized Management**: Single setting controls MFA for entire system
- **Instant Effect**: Changes take effect immediately
- **Audit Trail**: All MFA activities are logged

## Migration Strategy

### **For Existing Users**
1. **Enable System MFA**: Set `MFA_ENABLED=true`
2. **User Login**: Existing users will be prompted to set up MFA
3. **Setup Required**: Users must call `/api/v1/mfa/setup` before they can login
4. **Optional Disable**: Users can disable MFA if they choose

### **For New Users**
1. **Automatic Setup**: MFA is automatically enabled during signup
2. **No Setup Required**: Users can login immediately
3. **Optional Disable**: Users can disable MFA if they prefer

## Administration

### **Enabling Mandatory MFA**
1. Set `MFA_ENABLED=true` in environment variables
2. Restart the application
3. All new users automatically get MFA enabled
4. Existing users must set up MFA on next login

### **Disabling Mandatory MFA**
1. Set `MFA_ENABLED=false` in environment variables
2. Restart the application
3. All users can login without MFA
4. Existing MFA settings are preserved

### **Monitoring**
- Check MFA status endpoint for system-wide status
- Monitor user MFA setup completion
- Review login attempts and MFA verification logs
- Track users who have disabled MFA

## Troubleshooting

### **Common Issues**

1. **User Can't Login**
   - Check if MFA setup is required (`setup_required: true`)
   - Verify user has called `/api/v1/mfa/setup`
   - Check if Email OTP is enabled for user

2. **MFA Not Auto-Enabled for New Users**
   - Verify `MFA_ENABLED=true`
   - Check `MFA_EMAIL_OTP_ENABLED=true`
   - Review signup logs for MFA auto-enable errors

3. **Existing Users Stuck in Login Loop**
   - Check if user has MFA record in database
   - Verify `setup_required` status
   - Ensure user calls setup endpoint before login

### **Debug Information**
- Check `/api/v1/mfa/status` for current user status
- Review application logs for MFA auto-enable errors
- Verify database for MFA records
- Check email service configuration

## Future Enhancements

### **Planned Features**
1. **Admin Override**: Allow admins to force MFA for specific users
2. **Grace Period**: Temporary MFA bypass for new users
3. **User Groups**: Different MFA policies for different roles
4. **Compliance Reporting**: Track MFA adoption and usage

### **Advanced Options**
1. **Risk-Based**: Dynamic MFA requirements based on risk
2. **Device Trust**: Remember trusted devices
3. **Geolocation**: Location-based MFA requirements
4. **Time-Based**: MFA requirements based on time of day

## Support

For technical support:
- Check system MFA status via API
- Review application logs for detailed error information
- Verify email service configuration
- Check user MFA status and setup requirements
- Contact development team with specific error messages and timestamps

The mandatory MFA implementation provides **enhanced security** with **automatic protection** for all users while maintaining **user choice** and **administrative control**.
