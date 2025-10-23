# Multi-Factor Authentication (MFA) Implementation Guide

## Overview

This document provides a comprehensive guide to the Multi-Factor Authentication (MFA) implementation in the Recruiter AI Backend. The implementation follows industry standards and best practices for secure authentication.

## Features Implemented

### 1. Time-based One-Time Password (TOTP)
- **Standard**: RFC 6238 (TOTP)
- **Algorithm**: HMAC-SHA1
- **Time Window**: 30 seconds (configurable)
- **Tolerance**: ±1 time window (configurable)
- **QR Code Generation**: Automatic QR code generation for easy setup

### 2. Backup Codes
- **Count**: 10 codes (configurable)
- **Length**: 8 characters (configurable)
- **Storage**: SHA-256 hashed
- **Usage**: Single-use only
- **Regeneration**: Available with password verification

### 3. Security Features
- **Rate Limiting**: 5 failed attempts lockout (configurable)
- **Lockout Duration**: 15 minutes (configurable)
- **IP Tracking**: Login attempt logging with IP and User-Agent
- **Secure Storage**: All secrets encrypted and hashed
- **Token Management**: Short-lived MFA tokens (5 minutes)

## Architecture

### Database Models

#### 1. MFAModel (`user_mfa` table)
```sql
- id: Primary key
- user_id: Foreign key to users table
- totp_secret: Base32 encoded TOTP secret
- totp_enabled: Boolean flag
- totp_verified: Boolean flag
- backup_codes: JSON array of hashed backup codes
- backup_codes_generated: Boolean flag
- recovery_email: Optional recovery email
- recovery_phone: Optional recovery phone
- created_at, updated_at: Audit timestamps
```

#### 2. MFABackupCodeModel (`mfa_backup_codes` table)
```sql
- id: Primary key
- user_id: Foreign key to users table
- code_hash: SHA-256 hash of used backup code
- used_at: Timestamp when code was used
- created_at: Creation timestamp
```

#### 3. MFALoginAttemptModel (`mfa_login_attempts` table)
```sql
- id: Primary key
- user_id: Foreign key to users table
- attempt_type: 'totp', 'backup_code', or 'recovery'
- success: Boolean flag
- ip_address: Client IP address
- user_agent: Client user agent
- created_at: Attempt timestamp
```

### Service Layer

#### MFAService
The main service class handling all MFA operations:

- **TOTP Management**: Secret generation, QR code creation, verification
- **Backup Codes**: Generation, hashing, verification, regeneration
- **Login Verification**: TOTP and backup code verification
- **Rate Limiting**: Failed attempt tracking and lockout
- **Status Management**: MFA status checking and management

### API Endpoints

#### Authentication Flow
1. **POST /api/v1/auth/login** - Initial login (returns MFA token if MFA enabled)
2. **POST /api/v1/auth/login/mfa** - Complete MFA verification

#### MFA Management
1. **POST /api/v1/mfa/setup** - Initiate MFA setup
2. **POST /api/v1/mfa/verify** - Verify MFA setup
3. **POST /api/v1/mfa/disable** - Disable MFA
4. **GET /api/v1/mfa/status** - Get MFA status
5. **POST /api/v1/mfa/regenerate-backup-codes** - Regenerate backup codes

#### Recovery (Placeholder)
1. **POST /api/v1/mfa/recovery** - Initiate recovery
2. **POST /api/v1/mfa/recovery/verify** - Verify recovery

## Configuration

### Environment Variables
```python
# MFA Configuration
MFA_ENABLED=true
MFA_ISSUER_NAME="Recruiter AI"
MFA_TOTP_WINDOW=1  # Allow 1 time window before/after current
MFA_BACKUP_CODES_COUNT=10
MFA_BACKUP_CODE_LENGTH=8
MFA_MAX_LOGIN_ATTEMPTS=5
MFA_LOCKOUT_DURATION_MINUTES=15
MFA_REQUIRE_BACKUP_CODES=true
```

## Usage Examples

### 1. Setting Up MFA

#### Step 1: Initiate Setup
```bash
curl -X POST "http://localhost:8000/api/v1/mfa/setup" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json"
```

Response:
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_uri": "otpauth://totp/user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Recruiter%20AI",
  "backup_codes": ["a1b2c3d4", "e5f6g7h8", ...]
}
```

#### Step 2: Verify Setup
```bash
curl -X POST "http://localhost:8000/api/v1/mfa/verify" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"totp_code": "123456"}'
```

### 2. Login with MFA

#### Step 1: Initial Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

Response (if MFA enabled):
```json
{
  "access_token": null,
  "token_type": "bearer",
  "user": {...},
  "mfa_required": true,
  "mfa_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Step 2: Complete MFA Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/mfa" \
  -H "Content-Type: application/json" \
  -d '{"mfa_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", "mfa_code": "123456"}'
```

### 3. Using Backup Codes
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/mfa" \
  -H "Content-Type: application/json" \
  -d '{"mfa_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", "mfa_code": "a1b2c3d4"}'
```

## Security Considerations

### 1. Secret Storage
- TOTP secrets are stored in Base32 format
- Backup codes are hashed using SHA-256
- No plaintext secrets are stored in the database

### 2. Rate Limiting
- Maximum 5 failed attempts per user
- 15-minute lockout period
- IP and User-Agent tracking for audit

### 3. Token Management
- MFA tokens are short-lived (5 minutes)
- Separate from main access tokens
- Cannot be used for API access

### 4. Backup Code Security
- Single-use only
- Automatically marked as used
- Can be regenerated with password verification

## Dependencies

### Required Packages
```txt
pyotp>=2.9.0          # TOTP implementation
qrcode[pil]>=7.4.2    # QR code generation
```

### Installation
```bash
pip install pyotp qrcode[pil]
```

## Database Migration

Run the migration to create MFA tables:
```bash
alembic upgrade head
```

## Frontend Integration

### 1. QR Code Display
```javascript
// Generate QR code from URI
const qrCode = new QRCode(document.getElementById("qrcode"), {
  text: response.qr_code_uri,
  width: 256,
  height: 256
});
```

### 2. TOTP Input
```javascript
// 6-digit TOTP code input
const totpCode = document.getElementById("totp-code").value;
```

### 3. Login Flow
```javascript
// Step 1: Initial login
const loginResponse = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const loginData = await loginResponse.json();

if (loginData.mfa_required) {
  // Step 2: MFA verification
  const mfaResponse = await fetch('/api/v1/auth/login/mfa', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      mfa_token: loginData.mfa_token,
      mfa_code: totpCode
    })
  });
}
```

## Testing

### 1. Unit Tests
Test individual MFA service methods:
```python
def test_totp_verification():
    mfa_service = MFAService()
    secret = mfa_service.generate_totp_secret()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert mfa_service.verify_totp_code(secret, code)
```

### 2. Integration Tests
Test complete MFA flow:
```python
def test_mfa_login_flow():
    # Setup MFA
    # Login with password
    # Verify MFA code
    # Complete login
```

## Monitoring and Logging

### 1. Login Attempts
All MFA login attempts are logged with:
- User ID
- Attempt type (TOTP/backup code)
- Success/failure
- IP address
- User agent
- Timestamp

### 2. Security Events
Monitor for:
- Multiple failed attempts
- Backup code usage
- MFA setup/disabling
- Unusual login patterns

## Compliance

This implementation follows:
- **RFC 6238**: TOTP standard
- **NIST SP 800-63B**: Digital Identity Guidelines
- **OWASP**: Authentication security guidelines
- **SOC 2**: Security controls

## Troubleshooting

### Common Issues

1. **TOTP Code Not Working**
   - Check system time synchronization
   - Verify secret was entered correctly
   - Ensure app supports TOTP (not HOTP)

2. **Backup Codes Not Working**
   - Codes are single-use only
   - Check for typos in code entry
   - Regenerate if all codes used

3. **Account Locked**
   - Wait for lockout period to expire
   - Check for multiple failed attempts
   - Contact admin if persistent

### Support

For technical support or security concerns, contact the development team with:
- User ID (if applicable)
- Error messages
- Timestamp of issue
- Steps to reproduce

## Future Enhancements

### Planned Features
1. **SMS-based MFA**: SMS code delivery
2. **Email-based MFA**: Email code delivery
3. **Hardware Tokens**: FIDO2/WebAuthn support
4. **Biometric Authentication**: Fingerprint/face recognition
5. **Risk-based Authentication**: Adaptive MFA based on risk factors

### Configuration Options
1. **MFA Enforcement**: Per-role MFA requirements
2. **Grace Period**: Temporary MFA bypass for new users
3. **Device Trust**: Remember trusted devices
4. **Geolocation**: Location-based MFA requirements
