from fastapi import APIRouter

router = APIRouter()


@router.post("/", summary="Create persona (command)")
async def create_persona():
	return {"message": "stub: create_persona"}


@router.get("/{persona_id}", summary="Get persona (query)")
async def get_persona(persona_id: str):
	return {"message": "stub: get_persona", "persona_id": persona_id}
