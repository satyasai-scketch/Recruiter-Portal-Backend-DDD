from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


class UserSignup(BaseModel):
	email: EmailStr
	password: str = Field(min_length=8)
	first_name: str = Field(min_length=1, max_length=50)
	last_name: str = Field(min_length=1, max_length=50)
	phone: Optional[str] = Field(None, max_length=20)
	role_id: str = Field(description="ID of the user role")


class UserLogin(BaseModel):
	email: EmailStr
	password: str


class ForgotPasswordRequest(BaseModel):
	email: EmailStr


class ResetPasswordRequest(BaseModel):
	token: str
	new_password: str = Field(min_length=8)


class UserRead(BaseModel):
	id: str
	email: EmailStr
	first_name: str
	last_name: str
	phone: Optional[str] = None
	is_active: bool
	role_id: Optional[str] = None
	role_name: Optional[str] = None
	created_at: datetime
	updated_at: datetime


class LoginResponse(BaseModel):
	access_token: Optional[str] = None
	token_type: str
	user: UserRead
	mfa_required: bool = False
	mfa_token: Optional[str] = None


class PasswordResetResponse(BaseModel):
	message: str


class UserUpdate(BaseModel):
	email: Optional[EmailStr] = None
	first_name: Optional[str] = Field(None, min_length=1, max_length=50)
	last_name: Optional[str] = Field(None, min_length=1, max_length=50)
	phone: Optional[str] = Field(None, max_length=20)
	is_active: Optional[bool] = None
	role_id: Optional[str] = None


class MFALoginRequest(BaseModel):
	mfa_token: str
	mfa_code: str = Field(min_length=6, max_length=8, description="TOTP code or backup code")