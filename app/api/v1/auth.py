from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_db
from app.schemas.user import UserSignup, UserLogin, UserRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=UserRead, summary="User signup")
async def signup(payload: UserSignup, db: Session = Depends(get_db)):
	try:
		user = AuthService().signup(db, payload.email, payload.password, payload.role_name)
		return UserRead(id=user.id, email=user.email, is_active=user.is_active, role=(user.role.name if user.role else None))
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", summary="User login")
async def login(payload: UserLogin, db: Session = Depends(get_db)):
	try:
		token = AuthService().login(db, payload.email, payload.password)
		return {"access_token": token, "token_type": "bearer"}
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
