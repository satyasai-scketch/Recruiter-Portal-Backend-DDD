from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_mfa_user
from app.schemas.mfa import (
    MFAStatusResponse, EmailOTPSendRequest, EmailOTPSendResponse
)
from app.services.mfa_service import MFAService
from app.db.models.user import UserModel

router = APIRouter()


@router.get("/status", response_model=MFAStatusResponse, summary="Get MFA status")
async def get_mfa_status(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get MFA status for the current user.
    Shows system-level MFA configuration (read-only).
    """
    try:
        mfa_service = MFAService()
        status = mfa_service.get_mfa_status(db, current_user.id)
        return MFAStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/email-otp/send", response_model=EmailOTPSendResponse, summary="Send Email OTP for login")
async def send_email_otp(
    request: EmailOTPSendRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_mfa_user)
):
    """
    Send Email OTP to the current user during login flow.
    Can only be called with MFA token (not regular access token).
    """
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