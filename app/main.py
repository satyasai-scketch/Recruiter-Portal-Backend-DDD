from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import jd as jd_router
from app.api.v1 import persona as persona_router
from app.api.v1 import candidate as candidate_router
from app.api.v1 import match as match_router
from app.api.v1 import auth as auth_router
from app.core.logger import logger


app = FastAPI(title="Recruiter AI Backend", version="0.1.0")


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
	logger.error(f"ValueError on {request.url.path}: {exc}")
	return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
	logger.error(f"SQLAlchemyError on {request.url.path}: {exc}")
	return JSONResponse(status_code=500, content={"detail": "Database error"})


# Mount API routers
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(jd_router.router, prefix="/api/v1/jd", tags=["jd"])
app.include_router(persona_router.router, prefix="/api/v1/persona", tags=["persona"])
app.include_router(candidate_router.router, prefix="/api/v1/candidate", tags=["candidate"])
app.include_router(match_router.router, prefix="/api/v1/match", tags=["match"])


@app.get("/health")
async def health_check() -> dict:
	"""Liveness/readiness probe endpoint."""
	return {"status": "ok"}
