from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_db
from app.schemas.user import (
	UserSignup, UserLogin, UserRead, LoginResponse, 
	ForgotPasswordRequest, ResetPasswordRequest, PasswordResetResponse, UserUpdate
)
from app.services.auth_service import AuthService
from app.cqrs.handlers import handle_command, handle_query
from app.cqrs.commands.user_commands import UpdateUser
from app.cqrs.queries.user_queries import ListAllUsers, GetUser
from app.api.deps import get_current_user
from app.db.models.user import UserModel

router = APIRouter()


@router.post("/signup", response_model=UserRead, summary="User signup")
async def signup(payload: UserSignup, db: Session = Depends(get_db)):
	try:
		user = AuthService().signup(
			db, 
			payload.email, 
			payload.password, 
			payload.first_name,
			payload.last_name,
			payload.phone,
			payload.role_id
		)
		return UserRead(
			id=user.id, 
			email=user.email, 
			first_name=user.first_name,
			last_name=user.last_name,
			phone=user.phone,
			is_active=user.is_active, 
			role_id=user.role_id,
			role_name=(user.role.name if user.role else None),
			created_at=user.created_at,
			updated_at=user.updated_at
		)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=LoginResponse, summary="User login")
async def login(payload: UserLogin, db: Session = Depends(get_db)):
	try:
		auth_service = AuthService()
		token = auth_service.login(db, payload.email, payload.password)
		
		# Get user information
		user = auth_service.users.get_by_email(db, payload.email)
		user_info = UserRead(
			id=user.id,
			email=user.email,
			first_name=user.first_name,
			last_name=user.last_name,
			phone=user.phone,
			is_active=user.is_active,
			role_id=user.role_id,
			role_name=(user.role.name if user.role else None),
			created_at=user.created_at,
			updated_at=user.updated_at
		)
		
		return LoginResponse(
			access_token=token,
			token_type="bearer",
			user=user_info
		)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.post("/forgot-password", response_model=PasswordResetResponse, summary="Request password reset")
async def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
	"""Send password reset email to user."""
	try:
		AuthService().forgot_password(db, payload.email)
		return PasswordResetResponse(
			message="If the email exists, a password reset link has been sent."
		)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-password", response_model=PasswordResetResponse, summary="Reset password with token")
async def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
	"""Reset password using token from email."""
	try:
		AuthService().reset_password(db, payload.token, payload.new_password)
		return PasswordResetResponse(
			message="Password has been reset successfully."
		)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=list[UserRead], summary="Get all users")
async def get_all_users(
	skip: int = 0,
	limit: int = 100,
	db: Session = Depends(db_session),
	current_user: UserModel = Depends(get_current_user)
):
	"""Get all users with pagination."""
	try:
		users = handle_query(db, ListAllUsers(skip=skip, limit=limit))
		return [
			UserRead(
				id=user.id,
				email=user.email,
				first_name=user.first_name,
				last_name=user.last_name,
				phone=user.phone,
				is_active=user.is_active,
				role_id=user.role_id,
				role_name=(user.role.name if user.role else None),
				created_at=user.created_at,
				updated_at=user.updated_at
			)
			for user in users
		]
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.patch("/users/{user_id}", response_model=UserRead, summary="Update user")
async def update_user(
	user_id: str,
	payload: UserUpdate,
	db: Session = Depends(db_session),
	current_user: UserModel = Depends(get_current_user)
):
	"""Update a user by ID."""
	try:
		# Convert Pydantic model to dict, excluding None values
		update_data = payload.model_dump(exclude_unset=True)
		
		# Use the command handler to update the user
		updated_user = handle_command(db, UpdateUser(user_id, update_data))
		
		if not updated_user:
			raise HTTPException(status_code=404, detail="User not found")
		
		return UserRead(
			id=updated_user.id,
			email=updated_user.email,
			first_name=updated_user.first_name,
			last_name=updated_user.last_name,
			phone=updated_user.phone,
			is_active=updated_user.is_active,
			role_id=updated_user.role_id,
			role_name=(updated_user.role.name if updated_user.role else None),
			created_at=updated_user.created_at,
			updated_at=updated_user.updated_at
		)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))
