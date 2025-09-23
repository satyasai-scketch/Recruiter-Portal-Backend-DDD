from fastapi import APIRouter

router = APIRouter()


@router.post("/score", summary="Score candidates (command)")
async def score_candidates():
	return {"message": "stub: score_candidates"}


@router.get("/recommendations", summary="Top recommendations (query)")
async def recommendations():
	return {"message": "stub: recommendations"}
