from fastapi import APIRouter

router = APIRouter()


@router.post("/", summary="Create job description (command)")
async def create_jd():
	return {"message": "stub: create_jd"}


@router.get("/{jd_id}", summary="Get job description (query)")
async def get_jd(jd_id: str):
	return {"message": "stub: get_jd", "jd_id": jd_id}
