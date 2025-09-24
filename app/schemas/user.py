from pydantic import BaseModel, EmailStr, Field
from typing import List


class UserSignup(BaseModel):
	email: EmailStr
	password: str = Field(min_length=8)


class UserLogin(BaseModel):
	email: EmailStr
	password: str


class UserRead(BaseModel):
	id: str
	email: EmailStr
	is_active: bool
	roles: List[str]
