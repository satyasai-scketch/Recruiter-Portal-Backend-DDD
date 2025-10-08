from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.schemas.persona import PersonaCreate, PersonaRead
from app.cqrs.handlers import handle_command, handle_query
from app.services.persona_service import PersonaService
from app.db.models.user import UserModel
from app.cqrs.commands.persona_commands import CreatePersona
from app.cqrs.queries.persona_queries import ListPersonasByJobDescription, ListAllPersonas, CountPersonas, GetPersona


router = APIRouter()


@router.post("/", response_model=PersonaRead, summary="Create persona (command)")
async def create_persona(
	payload: PersonaCreate, 
	db: Session = Depends(db_session),
	current_user: UserModel = Depends(get_current_user)
):
	# Always use nested creation for comprehensive persona data
	model = handle_command(db, CreatePersona(payload.model_dump(), current_user.id))
	# Fetch eagerly to return nested
	model = handle_query(db, GetPersona(model.id))
	return PersonaRead.model_validate(model)


@router.get("/by-jd/{jd_id}", response_model=list[PersonaRead], summary="List personas for a Job Description")
async def list_personas_by_jd(jd_id: str, db: Session = Depends(db_session)):
	models = handle_query(db, ListPersonasByJobDescription(jd_id))
	return [PersonaRead.model_validate(m) for m in models]
