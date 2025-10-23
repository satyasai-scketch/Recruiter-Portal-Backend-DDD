# app/schemas/mfa.py
from pydantic import BaseModel, Field
from typing import List, Optional


class MFASetupResponse(BaseModel):
    """Response for MFA setup initiation."""
    secret: str = Field(description="TOTP secret key")
    qr_code_uri: str = Field(description="URI for QR code generation")
    backup_codes: List[str] = Field(description="List of backup codes (show only once)")


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA setup."""
    totp_code: str = Field(min_length=6, max_length=6, description="6-digit TOTP code")


class MFAVerifyResponse(BaseModel):
    """Response for MFA verification."""
    success: bool
    message: str


class MFALoginRequest(BaseModel):
    """Request for MFA login verification."""
    mfa_code: str = Field(min_length=6, max_length=8, description="TOTP code or backup code")


class MFALoginResponse(BaseModel):
    """Response for MFA login verification."""
    success: bool
    message: str


class MFADisableRequest(BaseModel):
    """Request to disable MFA."""
    password: str = Field(description="User password for verification")


class MFADisableResponse(BaseModel):
    """Response for MFA disable."""
    success: bool
    message: str


class MFARegenerateBackupCodesRequest(BaseModel):
    """Request to regenerate backup codes."""
    password: str = Field(description="User password for verification")


class MFARegenerateBackupCodesResponse(BaseModel):
    """Response for backup codes regeneration."""
    backup_codes: List[str] = Field(description="New backup codes (show only once)")
    message: str


class MFAStatusResponse(BaseModel):
    """Response for MFA status check."""
    enabled: bool = Field(description="Whether MFA is enabled for this user")
    system_enabled: bool = Field(description="Whether MFA is enabled system-wide")
    email_otp_enabled: bool = Field(description="Whether Email OTP is enabled for this user")
    email_otp_verified: bool = Field(description="Whether Email OTP is verified for this user")
    backup_codes_generated: bool = Field(description="Whether backup codes are generated")
    backup_codes_remaining: int = Field(description="Number of unused backup codes")
    setup_required: bool = Field(description="Whether MFA setup is required for this user")


class EmailOTPEnableRequest(BaseModel):
    """Request to enable Email OTP."""
    pass  # No additional parameters needed


class EmailOTPEnableResponse(BaseModel):
    """Response for Email OTP enable."""
    success: bool
    message: str


class EmailOTPDisableRequest(BaseModel):
    """Request to disable Email OTP."""
    password: str = Field(description="User password for verification")


class EmailOTPDisableResponse(BaseModel):
    """Response for Email OTP disable."""
    success: bool
    message: str


class EmailOTPSendRequest(BaseModel):
    """Request to send Email OTP."""
    pass  # No additional parameters needed


class EmailOTPSendResponse(BaseModel):
    """Response for Email OTP send."""
    success: bool
    message: str


class EmailOTPVerifyRequest(BaseModel):
    """Request to verify Email OTP."""
    otp_code: str = Field(min_length=4, max_length=8, description="Email OTP code")


class EmailOTPVerifyResponse(BaseModel):
    """Response for Email OTP verification."""
    success: bool
    message: str


class BackupCodesGenerateResponse(BaseModel):
    """Response for backup codes generation."""
    backup_codes: List[str] = Field(description="New backup codes (show only once)")
    message: str


class MFARecoveryRequest(BaseModel):
    """Request for MFA recovery."""
    email: str = Field(description="User email")
    recovery_method: str = Field(description="Recovery method: 'email' or 'phone'")


class MFARecoveryResponse(BaseModel):
    """Response for MFA recovery."""
    success: bool
    message: str
    recovery_token: Optional[str] = None


class MFARecoveryVerifyRequest(BaseModel):
    """Request to verify MFA recovery."""
    recovery_token: str = Field(description="Recovery token")
    recovery_code: str = Field(description="Recovery code sent via email/SMS")


class MFARecoveryVerifyResponse(BaseModel):
    """Response for MFA recovery verification."""
    success: bool
    message: str
    temp_access_token: Optional[str] = None
