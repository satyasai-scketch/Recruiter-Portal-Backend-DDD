from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class UserSignup(BaseModel):
	email: EmailStr
	password: str = Field(min_length=8)
	role_name: Optional[str] = None


class UserLogin(BaseModel):
	email: EmailStr
	password: str


class UserRead(BaseModel):
	id: str
	email: EmailStr
	is_active: bool
	role: Optional[str] = None
