from pydantic import BaseModel, Field


class MFAStatusResponse(BaseModel):
    """Response for MFA status check."""
    enabled: bool = Field(description="Whether MFA is enabled (system-level)")
    system_enabled: bool = Field(description="Whether MFA is enabled system-wide")
    email_otp_enabled: bool = Field(description="Whether Email OTP is enabled")


class MFALoginRequest(BaseModel):
    """Request for MFA login verification."""
    mfa_token: str = Field(description="Temporary MFA token from initial login")
    mfa_code: str = Field(min_length=4, max_length=8, description="Email OTP code")


class MFALoginResponse(BaseModel):
    """Response for MFA login verification."""
    success: bool
    message: str


class EmailOTPSendRequest(BaseModel):
    """Request to send Email OTP."""
    pass  # No additional parameters needed


class EmailOTPSendResponse(BaseModel):
    """Response for Email OTP send."""
    success: bool
    message: str