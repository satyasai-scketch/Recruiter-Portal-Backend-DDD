from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.schemas.persona import PersonaCreate, PersonaRead, PersonaUpdate, PersonaChangeLogRead, PersonaDeletionStats
from app.cqrs.handlers import handle_command, handle_query
from app.services.persona_service import PersonaService
from app.db.models.user import UserModel
from app.cqrs.commands.persona_commands import CreatePersona, UpdatePersona, DeletePersona
from app.cqrs.queries.persona_queries import ListPersonasByJobDescription, ListAllPersonas, CountPersonas, GetPersona, GetPersonaChangeLogs, ListPersonasByJobRole

from app.cqrs.commands.generate_persona_from_jd import GeneratePersonaFromJD
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
@router.post("/generate-from-jd/{jd_id}", response_model=PersonaRead, summary="Generate persona from JD (preview, not saved)")
async def generate_persona_from_jd(
    jd_id: str,
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Generate persona structure from JD using AI.
    Returns the structure WITHOUT saving to database.
    """
    # Generate persona structure
    persona_data = handle_command(db, GeneratePersonaFromJD(jd_id=jd_id))
    
    # Remove analysis_insights (not part of PersonaRead schema)
    persona_data.pop('analysis_insights', None)
    
    # Add mock ID and user info for PersonaRead validation
    persona_data['id'] = 'preview'  # Or generate temp UUID
    persona_data['created_by'] = current_user.id
    persona_data['role_name'] = None  # Will be fetched when actually saved
    
    return PersonaRead.model_validate(persona_data)

@router.get("/", response_model=list[PersonaRead], summary="Get all personas")
async def get_all_personas(db: Session = Depends(db_session)):
	models = handle_query(db, ListAllPersonas())
	return [PersonaRead.model_validate(m) for m in models]


@router.get("/{persona_id}", response_model=PersonaRead, summary="Get persona by ID")
async def get_persona(persona_id: str, db: Session = Depends(db_session)):
	model = handle_query(db, GetPersona(persona_id))
	if model is None:
		from fastapi import HTTPException
		raise HTTPException(status_code=404, detail=f"Persona with ID '{persona_id}' not found")
	return PersonaRead.model_validate(model)


@router.get("/by-jd/{jd_id}", response_model=list[PersonaRead], summary="List personas for a Job Description")
async def list_personas_by_jd(jd_id: str, db: Session = Depends(db_session)):
	models = handle_query(db, ListPersonasByJobDescription(jd_id))
	return [PersonaRead.model_validate(m) for m in models]


@router.get("/by-role/{role_id}", response_model=list[PersonaRead], summary="List personas for a Job Role")
async def list_personas_by_role(role_id: str, db: Session = Depends(db_session)):
	"""List all personas associated with a specific job role.
	
	This endpoint retrieves all personas that are linked to job descriptions
	that use the specified job role. The query uses an optimized JOIN between
	personas and job_descriptions tables for better performance.
	
	Args:
		role_id: The ID of the job role to filter personas by
		
	Returns:
		List of PersonaRead objects containing all personas for the specified role
	"""
	models = handle_query(db, ListPersonasByJobRole(role_id))
	return [PersonaRead.model_validate(m) for m in models]


@router.patch("/{persona_id}", response_model=PersonaRead, summary="Update persona with change tracking")
async def update_persona(
	persona_id: str,
	payload: PersonaUpdate,
	db: Session = Depends(db_session),
	current_user: UserModel = Depends(get_current_user)
):
	"""Update a persona with comprehensive change tracking.
	
	This endpoint tracks all changes made to the persona and its nested entities:
	- Persona-level fields (name, role_name)
	- Categories (modification only, no addition/deletion)
	- Category notes (single note per category, can be added, modified, or deleted)
	- Subcategories (can be added, modified, or deleted)
	- Subcategory skillsets (can be added, modified, or deleted)
	
	Structure:
	- Each Category has ONE note (one-to-one relationship via notes_id)
	- Skillsets belong to Subcategories (persona_subcategory_id in PersonaSkillsetModel)
	
	All changes are logged in the persona_change_logs table for audit purposes.
	"""
	# Convert Pydantic model to dict, excluding None values
	update_data = payload.model_dump(exclude_unset=True)
	
	# Use the command handler to update the persona
	model = handle_command(db, UpdatePersona(persona_id, update_data, current_user.id))
	
	# Fetch the updated model with all relationships
	updated_model = handle_query(db, GetPersona(model.id))
	return PersonaRead.model_validate(updated_model)


@router.get("/{persona_id}/change-logs", response_model=list[PersonaChangeLogRead], summary="Get change logs for a persona")
async def get_persona_change_logs(
	persona_id: str,
	db: Session = Depends(db_session)
):
	"""Get all change logs for a persona.
	
	Returns a list of all changes made to the persona and its nested entities,
	ordered by most recent changes first. Each change log entry includes:
	- Entity type (persona, category, subcategory, skillset, notes)
	- Entity ID
	- Field name that was changed
	- Old and new values
	- User who made the change
	- Timestamp of the change
	"""
	# First check if persona exists
	persona = handle_query(db, GetPersona(persona_id))
	if persona is None:
		from fastapi import HTTPException
		raise HTTPException(status_code=404, detail=f"Persona with ID '{persona_id}' not found")
	
	change_logs = handle_query(db, GetPersonaChangeLogs(persona_id))
	
	# Convert to response format with user details
	result = []
	for log in change_logs:
		log_data = {
			"id": log.id,
			"persona_id": log.persona_id,
			"entity_type": log.entity_type,
			"entity_id": log.entity_id,
			"field_name": log.field_name,
			"old_value": log.old_value,
			"new_value": log.new_value,
			"changed_by": log.changed_by,
			"changed_at": log.changed_at,
			"changed_by_user": None
		}
		
		# Add user details if available
		if log.user:
			log_data["changed_by_user"] = {
				"id": log.user.id,
				"email": log.user.email,
				"name": getattr(log.user, 'name', None) or f"{log.user.first_name} {log.user.last_name}".strip() or log.user.email
			}
		
		result.append(PersonaChangeLogRead(**log_data))
	
	return result


@router.delete("/{persona_id}", response_model=PersonaDeletionStats, summary="Delete persona with comprehensive feedback")
async def delete_persona(
	persona_id: str,
	db: Session = Depends(db_session),
	current_user: UserModel = Depends(get_current_user)
):
	"""Delete a persona and all its associated data with comprehensive feedback.
	
	This endpoint will:
	1. Delete the persona and all its nested entities (categories, subcategories, skillsets, notes, change logs)
	2. Delete any external references (e.g., scores)
	3. Provide detailed feedback on what was deleted
	
	The deletion is comprehensive and will remove:
	- The main persona record
	- All persona categories and their subcategories
	- All persona skillsets (both category-level and subcategory-level)
	- All persona notes
	- All persona change logs
	- Any candidate scores associated with this persona
	
	Returns detailed statistics about what was deleted for verification.
	"""
	try:
		# Use the command handler to delete the persona
		deletion_stats = handle_command(db, DeletePersona(persona_id))
		
		return PersonaDeletionStats(**deletion_stats)
		
	except ValueError as e:
		from fastapi import HTTPException
		raise HTTPException(status_code=404, detail=str(e))
	except Exception as e:
		from fastapi import HTTPException
		raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
