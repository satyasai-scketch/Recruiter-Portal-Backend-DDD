from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path

from app.api.v1 import jd as jd_router
from app.api.v1 import persona as persona_router
from app.api.v1 import persona_level as persona_level_router
from app.api.v1 import candidate as candidate_router
from app.api.v1 import match as match_router
from app.api.v1 import auth as auth_router
from app.api.v1 import mfa as mfa_router
from app.api.v1 import company as company_router
from app.api.v1 import job_role as job_role_router
from app.api.v1 import role as role_router
from app.core.logger import logger
from app.core.config import settings


app = FastAPI(title="Recruiter AI Backend", version="0.1.0")

# Configure CORS - Allow all origins for now (to be restricted later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


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
app.include_router(mfa_router.router, prefix="/api/v1/mfa", tags=["mfa"])
app.include_router(jd_router.router, prefix="/api/v1/jd", tags=["jd"])
app.include_router(persona_router.router, prefix="/api/v1/persona", tags=["persona"])
app.include_router(persona_level_router.router, prefix="/api/v1/persona-level", tags=["persona-level"])
app.include_router(candidate_router.router, prefix="/api/v1/candidate", tags=["candidate"])
app.include_router(match_router.router, prefix="/api/v1/match", tags=["match"])
app.include_router(company_router.router, prefix="/api/v1/company", tags=["company"])
app.include_router(job_role_router.router, prefix="/api/v1/job-role", tags=["job-role"])
app.include_router(role_router.router, prefix="/api/v1/role", tags=["role"])

# Mount static files for local storage (only when using local storage)
if settings.STORAGE_TYPE.lower() == "local":
	# Ensure uploads directory exists
	uploads_path = Path(settings.LOCAL_STORAGE_PATH).parent
	uploads_path.mkdir(parents=True, exist_ok=True)
	
	# Mount static files
	app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")


@app.get("/health")
async def health_check() -> dict:
	"""Liveness/readiness probe endpoint."""
	return {"status": "ok"}


@app.get("/storage/info")
async def storage_info() -> dict:
	"""Get information about the current storage configuration."""
	from app.services.storage import StorageFactory
	
	try:
		storage_service = StorageFactory.get_storage_service()
		info = storage_service.get_storage_info()
		
		# Add configuration validation
		validation = StorageFactory.validate_storage_config()
		info['config_valid'] = validation['valid']
		info['config_errors'] = validation.get('errors', [])
		
		return info
	except Exception as e:
		return {
			"error": str(e),
			"storage_type": settings.STORAGE_TYPE
		}
