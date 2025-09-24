from fastapi import FastAPI

from app.api.v1 import jd as jd_router
from app.api.v1 import persona as persona_router
from app.api.v1 import candidate as candidate_router
from app.api.v1 import match as match_router
from app.api.v1 import auth as auth_router


app = FastAPI(title="Recruiter AI Backend", version="0.1.0")


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
