from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.persona import PersonaCreate, PersonaRead
from app.cqrs.handlers import CreatePersona, handle_command

router = APIRouter()


@router.post("/", response_model=PersonaRead, summary="Create persona (command)")
async def create_persona(payload: PersonaCreate, db: Session = Depends(db_session)):
	model = handle_command(db, CreatePersona(payload.dict()))
	return PersonaRead(
		id=model.id,
		job_description_id=model.job_description_id,
		name=model.name,
		weights=model.weights,
		intervals=model.intervals,
	)


@router.get("/{persona_id}", summary="Get persona (query)")
async def get_persona(persona_id: str):
	return {"message": "stub: get_persona", "persona_id": persona_id}
