from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


class UserSignup(BaseModel):
	email: EmailStr
	password: str = Field(min_length=8)
	first_name: str = Field(min_length=1, max_length=50)
	last_name: str = Field(min_length=1, max_length=50)
	phone: Optional[str] = Field(None, max_length=20)
	role_name: Optional[str] = None


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
	role: Optional[str] = None
	created_at: datetime
	updated_at: datetime


class LoginResponse(BaseModel):
	access_token: str
	token_type: str
	user: UserRead


class PasswordResetResponse(BaseModel):
	message: str
