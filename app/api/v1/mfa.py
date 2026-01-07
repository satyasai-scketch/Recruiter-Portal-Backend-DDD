# app/api/v1/mfa.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_mfa_user
from app.schemas.mfa import (
    MFASetupResponse, MFAVerifyRequest, MFAVerifyResponse,
    MFALoginRequest, MFALoginResponse, MFADisableRequest, MFADisableResponse,
    MFARegenerateBackupCodesRequest, MFARegenerateBackupCodesResponse,
    MFAStatusResponse, MFARecoveryRequest, MFARecoveryResponse,
    MFARecoveryVerifyRequest, MFARecoveryVerifyResponse,
    EmailOTPEnableRequest, EmailOTPEnableResponse, EmailOTPDisableRequest, EmailOTPDisableResponse,
    EmailOTPSendRequest, EmailOTPSendResponse, EmailOTPVerifyRequest, EmailOTPVerifyResponse,
    BackupCodesGenerateResponse
)
from app.services.mfa_service import MFAService
from app.db.models.user import UserModel
from app.core.config import settings

router = APIRouter()


# TOTP endpoints removed - only Email OTP is available
# TOTP functionality is kept in the service layer for future use


@router.get("/status", response_model=MFAStatusResponse, summary="Get MFA status")
async def get_mfa_status(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Get MFA status for the current user."""
    try:
        mfa_service = MFAService()
        status = mfa_service.get_mfa_status(db, current_user.id)
        
        return MFAStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/recovery", response_model=MFARecoveryResponse, summary="Initiate MFA recovery")
async def initiate_mfa_recovery(
    request: MFARecoveryRequest,
    db: Session = Depends(get_db)
):
    """Initiate MFA recovery process."""
    if not settings.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is not enabled")
    
    # This would typically send a recovery code via email or SMS
    # For now, we'll return a placeholder response
    return MFARecoveryResponse(
        success=True,
        message="Recovery process initiated. Check your email for recovery instructions.",
        recovery_token=None  # Would be generated in a real implementation
    )


@router.post("/recovery/verify", response_model=MFARecoveryVerifyResponse, summary="Verify MFA recovery")
async def verify_mfa_recovery(
    request: MFARecoveryVerifyRequest,
    db: Session = Depends(get_db)
):
    """Verify MFA recovery code."""
    if not settings.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is not enabled")
    
    # This would verify the recovery code and provide temporary access
    # For now, we'll return a placeholder response
    return MFARecoveryVerifyResponse(
        success=True,
        message="Recovery verification successful",
        temp_access_token=None  # Would be generated in a real implementation
    )


@router.post("/backup-codes/generate", response_model=BackupCodesGenerateResponse, summary="Generate new backup codes")
async def generate_backup_codes(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Generate new backup codes for the current user."""
    try:
        mfa_service = MFAService()
        backup_codes = mfa_service.generate_backup_codes_for_user(db, current_user.id)
        
        return BackupCodesGenerateResponse(
            backup_codes=backup_codes,
            message="New backup codes have been generated successfully. Please save them securely."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


# Email OTP Endpoints

@router.post("/setup", response_model=EmailOTPEnableResponse, summary="Setup MFA for user (mandatory when system MFA is enabled)")
async def setup_mfa(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Setup MFA for the current user (mandatory when system MFA is enabled)."""
    try:
        mfa_service = MFAService()
        success = mfa_service.enable_email_otp(db, current_user.id)
        
        if success:
            return EmailOTPEnableResponse(
                success=True,
                message="MFA has been successfully set up and enabled"
            )
        else:
            return EmailOTPEnableResponse(
                success=False,
                message="Failed to setup MFA"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/email-otp/enable", response_model=EmailOTPEnableResponse, summary="Enable Email OTP")
async def enable_email_otp(
    request: EmailOTPEnableRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Enable Email OTP for the current user."""
    try:
        mfa_service = MFAService()
        success = mfa_service.enable_email_otp(db, current_user.id)
        
        if success:
            return EmailOTPEnableResponse(
                success=True,
                message="Email OTP has been successfully enabled"
            )
        else:
            return EmailOTPEnableResponse(
                success=False,
                message="Failed to enable Email OTP"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/email-otp/disable", response_model=EmailOTPDisableResponse, summary="Disable Email OTP")
async def disable_email_otp(
    request: EmailOTPDisableRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Disable Email OTP for the current user."""
    try:
        mfa_service = MFAService()
        success = mfa_service.disable_email_otp(db, current_user.id)
        
        if success:
            return EmailOTPDisableResponse(
                success=True,
                message="Email OTP has been successfully disabled"
            )
        else:
            return EmailOTPDisableResponse(
                success=False,
                message="Failed to disable Email OTP"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/email-otp/send", response_model=EmailOTPSendResponse, summary="Send Email OTP")
async def send_email_otp(
    request: EmailOTPSendRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_mfa_user)
):
    """Send Email OTP to the current user."""
    try:
        mfa_service = MFAService()
        success = mfa_service.send_email_otp(db, current_user.id)
        
        if success:
            return EmailOTPSendResponse(
                success=True,
                message="Email OTP has been sent successfully"
            )
        else:
            return EmailOTPSendResponse(
                success=False,
                message="Failed to send Email OTP"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/email-otp/verify", response_model=EmailOTPVerifyResponse, summary="Verify Email OTP")
async def verify_email_otp(
    request: EmailOTPVerifyRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """Verify Email OTP code."""
    try:
        mfa_service = MFAService()
        success = mfa_service.verify_email_otp(db, current_user.id, request.otp_code)
        
        if success:
            return EmailOTPVerifyResponse(
                success=True,
                message="Email OTP verification successful"
            )
        else:
            return EmailOTPVerifyResponse(
                success=False,
                message="Invalid Email OTP code"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
