from fastapi import APIRouter

router = APIRouter()


@router.post("/upload", summary="Upload candidate CVs (command)")
async def upload_cvs():
	return {"message": "stub: upload_cvs"}


@router.get("/", summary="List candidates (query)")
async def list_candidates():
	return {"message": "stub: list_candidates"}
