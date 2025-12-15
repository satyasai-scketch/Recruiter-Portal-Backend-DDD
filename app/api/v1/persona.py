from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.api.deps import db_session, get_current_user
from app.api.deps_authorization import require_jd_access
from app.core.authorization import can_access_jd
from app.schemas.persona import PersonaCreate, PersonaRead, PersonaUpdate, PersonaChangeLogRead, PersonaDeletionStats, PersonaListResponse
from app.cqrs.handlers import handle_command, handle_query
from app.services.persona_service import PersonaService
from app.db.models.user import UserModel
from app.db.models.persona import PersonaModel
from app.cqrs.commands.persona_commands import CreatePersona, UpdatePersona, DeletePersona
from app.cqrs.queries.persona_queries import ListPersonasByJobDescription, ListAllPersonas, CountPersonas, GetPersona, GetPersonaChangeLogs, ListPersonasByJobRole
from fastapi import Query

from app.cqrs.commands.generate_persona_from_jd import GeneratePersonaFromJD
from app.schemas.persona_warning import (
    GenerateWarningsRequest,
    GenerateWarningsResponse,
    GetWarningResponse,
    PersonaWarningRead,
    LinkWarningsRequest,
    LinkWarningsResponse,
	GetOrGenerateWarningRequest
)
from app.cqrs.commands.persona_warning_commands import GeneratePersonaWarnings, LinkWarningsToPersona
from app.cqrs.queries.persona_warning_queries import GetWarningByEntity, ListWarningsByPersona, GetOrGenerateWarning


router = APIRouter()


def _convert_persona_model_to_read(model: PersonaModel, db: Session, candidate_counts: dict | None = None) -> PersonaRead:
	"""Convert PersonaModel to PersonaRead with all required fields."""
	# Get JD name from relationship
	jd_name = None
	if model.job_description:
		jd_name = model.job_description.title
	
	# Get creator name from relationship
	created_by_name = None
	if model.creator:
		# Construct full name from first_name and last_name
		if model.creator.first_name and model.creator.last_name:
			created_by_name = f"{model.creator.first_name} {model.creator.last_name}".strip()
		elif model.creator.first_name:
			created_by_name = model.creator.first_name
		elif model.creator.last_name:
			created_by_name = model.creator.last_name
		else:
			created_by_name = model.creator.email
	
	# Get updater name from relationship
	updated_by_name = None
	if model.updater:
		# Construct full name from first_name and last_name
		if model.updater.first_name and model.updater.last_name:
			updated_by_name = f"{model.updater.first_name} {model.updater.last_name}".strip()
		elif model.updater.first_name:
			updated_by_name = model.updater.first_name
		elif model.updater.last_name:
			updated_by_name = model.updater.last_name
		else:
			updated_by_name = model.updater.email
	
	# Count candidates evaluated against this persona (prefer precomputed map)
	candidate_count = None
	if candidate_counts is not None:
		candidate_count = candidate_counts.get(model.id)
	if candidate_count is None:
		persona_service = PersonaService()
		candidate_count = persona_service.count_candidates_for_persona(db, model.id)
	
	# Build PersonaRead dict
	persona_dict = {
		"id": model.id,
		"job_description_id": model.job_description_id,
		"jd_name": jd_name,
		"name": model.name,
		"role_name": model.role_name,
		"role_id": model.role_id,
		"created_at": model.created_at,
		"created_by": model.created_by,
		"created_by_name": created_by_name,
		"updated_at": model.updated_at,
		"updated_by": model.updated_by,
		"updated_by_name": updated_by_name,
		"is_active": model.is_active,
		"candidate_count": candidate_count,
		"categories": [cat for cat in model.categories] if hasattr(model, 'categories') else [],
		"persona_notes": model.persona_notes
	}
	
	return PersonaRead.model_validate(persona_dict)


@router.post("/", response_model=PersonaRead, summary="Create persona (command)")
async def create_persona(
	payload: PersonaCreate, 
	db: Session = Depends(db_session),
	current_user: UserModel = Depends(get_current_user)
):
	try:
		# Always use nested creation for comprehensive persona data
		model = handle_command(db, CreatePersona(payload.model_dump(), current_user.id))
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc))
	# Fetch eagerly to return nested
	model = handle_query(db, GetPersona(model.id))
	return _convert_persona_model_to_read(model, db)
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
    # Ensure contextvars are set before calling sync handler
    # FastAPI preserves contextvars in async->sync calls, but we ensure they're set here
    from app.core.context import request_user_id, request_db_session
    request_user_id.set(current_user.id)
    request_db_session.set(db)
    
    # Generate persona structure
    persona_data = handle_command(db, GeneratePersonaFromJD(jd_id=jd_id))
    
    # Remove analysis_insights (not part of PersonaRead schema)
    persona_data.pop('analysis_insights', None)
    
    # Add mock ID and user info for PersonaRead validation
    persona_data['id'] = 'preview'  # Or generate temp UUID
    persona_data['created_by'] = current_user.id
    persona_data['role_name'] = None  # Will be fetched when actually saved
    persona_data['created_at'] = datetime.now()
    return PersonaRead.model_validate(persona_data)

@router.get("/", response_model=PersonaListResponse, summary="Get all personas with pagination (role-based access)")
async def get_all_personas(
	page: int = Query(1, ge=1, description="Page number"),
	size: int = Query(10, ge=1, le=100, description="Page size"),
	db: Session = Depends(db_session),
	user: UserModel = Depends(get_current_user)
):
	"""
	List personas accessible to the current user with pagination.
	
	Access rules:
	- Admin/Recruiter: Can see all personas
	- Hiring Manager: Can only see personas for JDs they created or are assigned to
	
	Uses optimized SQL filtering directly in database instead of fetching all accessible IDs first.
	"""
	skip = (page - 1) * size
	
	# Use service with access filtering (pass user directly for optimized SQL filtering)
	persona_service = PersonaService()
	models = persona_service.list_all(db, skip, size, user)
	total = persona_service.count(db, user)
	candidate_counts = persona_service.count_candidates_for_personas(db, [m.id for m in models])
	
	# Convert to response format with all required fields
	persona_reads = [_convert_persona_model_to_read(m, db, candidate_counts) for m in models]
	
	return PersonaListResponse(
		personas=persona_reads,
		total=total,
		page=page,
		size=size,
		has_next=(skip + size) < total,
		has_prev=page > 1
	)


@router.get("/{persona_id}", response_model=PersonaRead, summary="Get persona by ID")
async def get_persona(
	persona_id: str,
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	Get a specific persona by ID.
	
	Access rules:
	- Admin/Recruiter: Can access any persona
	- Hiring Manager: Can only access personas for JDs they created or are assigned to
	"""
	model = handle_query(db, GetPersona(persona_id))
	if model is None:
		from fastapi import HTTPException
		raise HTTPException(status_code=404, detail=f"Persona with ID '{persona_id}' not found")
	
	# Check if user can access the JD associated with this persona
	# First verify JD exists, then check access
	from app.repositories.job_description_repo import SQLAlchemyJobDescriptionRepository
	jd_repo = SQLAlchemyJobDescriptionRepository()
	jd = jd_repo.get(db, model.job_description_id)
	
	if not jd:
		# JD doesn't exist (shouldn't happen if persona exists, but handle gracefully)
		from fastapi import HTTPException
		raise HTTPException(status_code=404, detail="Associated job description not found")
	
	if not can_access_jd(db, user, model.job_description_id):
		# JD exists but user doesn't have access
		from fastapi import HTTPException, status
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Access denied. You do not have permission to access this persona."
		)
	
	return _convert_persona_model_to_read(model, db)


@router.get("/by-jd/{jd_id}", response_model=list[PersonaRead], summary="List personas for a Job Description")
async def list_personas_by_jd(
	jd_id: str = Depends(require_jd_access),
	db: Session = Depends(db_session),
	user=Depends(get_current_user)
):
	"""
	List personas for a specific job description.
	
	Access rules:
	- Admin/Recruiter: Can access personas for any JD
	- Hiring Manager: Can only access personas for JDs they created or are assigned to
	"""
	models = handle_query(db, ListPersonasByJobDescription(jd_id))
	persona_service = PersonaService()
	candidate_counts = persona_service.count_candidates_for_personas(db, [m.id for m in models])
	return [_convert_persona_model_to_read(m, db, candidate_counts) for m in models]


@router.get("/by-role/{role_id}", response_model=list[PersonaRead], summary="List personas for a Job Role")
async def list_personas_by_role(
	role_id: str,
	db: Session = Depends(db_session),
	user: UserModel = Depends(get_current_user)
):
	"""List all personas associated with a specific job role.
	
	Access rules:
	- Admin/Recruiter: Can see all personas for any role
	- Hiring Manager: Can only see personas for JDs they created or are assigned to
	
	This endpoint retrieves all personas that are linked to job descriptions
	that use the specified job role. The query uses an optimized JOIN between
	personas and job_descriptions tables for better performance.
	
	Args:
		role_id: The ID of the job role to filter personas by
		
	Returns:
		List of PersonaRead objects containing all personas for the specified role
	"""
	# Apply access filtering based on user role
	persona_service = PersonaService()
	all_models = handle_query(db, ListPersonasByJobRole(role_id))
	
	# Filter based on user access
	accessible_models = []
	for model in all_models:
		if can_access_jd(db, user, model.job_description_id):
			accessible_models.append(model)
	
	persona_service = PersonaService()
	candidate_counts = persona_service.count_candidates_for_personas(db, [m.id for m in accessible_models])
	return [_convert_persona_model_to_read(m, db, candidate_counts) for m in accessible_models]


@router.patch("/{persona_id}", response_model=PersonaRead, summary="Update persona with change tracking")
async def update_persona(
	persona_id: str,
	payload: PersonaUpdate,
	db: Session = Depends(db_session),
	current_user: UserModel = Depends(get_current_user)
):
	"""Update a persona with comprehensive change tracking.
	
	Access rules:
	- Admin/Recruiter: Can update any persona
	- Hiring Manager: Can only update personas for JDs they created or are assigned to
	
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
	# First check if persona exists
	persona = handle_query(db, GetPersona(persona_id))
	if persona is None:
		from fastapi import HTTPException
		raise HTTPException(status_code=404, detail=f"Persona with ID '{persona_id}' not found")
	
	# Check if user can access the JD associated with this persona
	if not can_access_jd(db, current_user, persona.job_description_id):
		from fastapi import HTTPException, status
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Access denied. You do not have permission to update this persona."
		)
	
	# Convert Pydantic model to dict, excluding None values
	update_data = payload.model_dump(exclude_unset=True)
	
	# Use the command handler to update the persona
	model = handle_command(db, UpdatePersona(persona_id, update_data, current_user.id))
	
	# Fetch the updated model with all relationships
	updated_model = handle_query(db, GetPersona(model.id))
	return _convert_persona_model_to_read(updated_model, db)


@router.get("/{persona_id}/change-logs", response_model=list[PersonaChangeLogRead], summary="Get change logs for a persona")
async def get_persona_change_logs(
	persona_id: str,
	db: Session = Depends(db_session),
	user: UserModel = Depends(get_current_user)
):
	"""Get all change logs for a persona.
	
	Access rules:
	- Admin/Recruiter: Can access change logs for any persona
	- Hiring Manager: Can only access change logs for personas they have access to
	
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
	
	# Check if user can access the JD associated with this persona
	if not can_access_jd(db, user, persona.job_description_id):
		from fastapi import HTTPException, status
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Access denied. You do not have permission to access this persona's change logs."
		)
	
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
	
	Access rules:
	- Admin/Recruiter: Can delete any persona
	- Hiring Manager: Can only delete personas for JDs they created or are assigned to
	
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
		# First check if persona exists
		persona = handle_query(db, GetPersona(persona_id))
		if persona is None:
			from fastapi import HTTPException
			raise HTTPException(status_code=404, detail=f"Persona with ID '{persona_id}' not found")
		
		# Check if user can access the JD associated with this persona
		if not can_access_jd(db, current_user, persona.job_description_id):
			from fastapi import HTTPException, status
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="Access denied. You do not have permission to delete this persona."
			)
		
		# Use the command handler to delete the persona
		deletion_stats = handle_command(db, DeletePersona(persona_id))
		
		return PersonaDeletionStats(**deletion_stats)
		
	except ValueError as e:
		from fastapi import HTTPException
		raise HTTPException(status_code=404, detail=str(e))
	except HTTPException:
		# Re-raise HTTP exceptions (like 403 Forbidden)
		raise
	except Exception as e:
		from fastapi import HTTPException
		raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
# ============ WARNING ENDPOINTS ============

@router.post("/warnings/generate", response_model=GenerateWarningsResponse, summary="Generate weight violation warnings")
async def generate_persona_warnings(
    payload: GenerateWarningsRequest,
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Generate warning messages for all weight violations in a persona.
    
    **When to call**: When the first weight violation is detected.
    
    **What it does**:
    - Analyzes the entire persona structure (categories, subcategories, weights, ranges)
    - Generates contextual warnings for each category/subcategory
    - Stores warnings with a temporary preview ID
    - Returns the preview ID for future queries
    
    **What happens**: LLM analyzes persona structure and generates messages like:
    - "Reducing Technical Skills below 30% may undervalue system design expertise..."
    - "Increasing Leadership above 40% may over-emphasize management at expense of technical depth..."
    """
    result = handle_command(
        db, 
        GeneratePersonaWarnings(persona_data=payload.persona_data)
    )
    return GenerateWarningsResponse.model_validate(result)

@router.post("/warnings/get-or-generate", response_model=GetWarningResponse)
async def get_or_generate_warning(
    payload: GetOrGenerateWarningRequest,
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    **RECOMMENDED**: Fetch warning if cached, generate on-demand if missing.
    
    Use this for real-time weight validation during persona editing.
    
    **Flow**:
    
    1️⃣ **First Violation** (must include entity_data):
    ```json
    {
      "persona_id": null,
      "entity_type": "subcategory",
      "entity_name": "Frontend Development",
      "violation_type": "below_min",
      "entity_data": {
        "name": "Frontend Development",
        "weight": 30,
        "range_min": -5,
        "range_max": 10,
        "level_id": "5",
        "parent_category": "Technical Skills",
        "technologies": ["React.js", "JavaScript (ES6+)", "HTML5", "CSS3"]
      }
    }
    ```
    Response: `{ "persona_id": "preview-abc123", "message": "...", "generated_now": true }`
    
    2️⃣ **Subsequent Violations - New Entity** (include entity_data):
    ```json
    {
      "persona_id": "preview-abc123",
      "entity_type": "category",
      "entity_name": "Leadership Skills",
      "violation_type": "above_max",
      "entity_data": {
        "name": "Leadership Skills",
        "weight": 25,
        "range_min": -2,
        "range_max": 4,
        "technologies": []
      }
    }
    ```
    Response: `{ "persona_id": "preview-abc123", "message": "...", "generated_now": true }`
    
    3️⃣ **Cached Lookup - Same Entity** (entity_data optional):
    ```json
    {
      "persona_id": "preview-abc123",
      "entity_type": "subcategory",
      "entity_name": "Frontend Development",
      "violation_type": "above_max"
      // ✅ NO entity_data needed - already generated!
    }
    ```
    Response: `{ "persona_id": "preview-abc123", "message": "...", "generated_now": false }`
    
    **entity_data Requirements**:
    - ✅ **REQUIRED**: When generating warning for first time
    - ❌ **OPTIONAL**: When fetching cached warning (same entity violated again)
    
    For **Categories**:
    ```typescript
    {
      name: string;           // Required
      weight: number;         // Required: current weight value
      range_min: number;      // Required
      range_max: number;      // Required
      technologies: []        // Empty array (categories don't have tech)
    }
    ```
    
    For **Subcategories**:
    ```typescript
    {
      name: string;                // Required
      weight: number;              // Required: current weight value
      range_min: number;           // Required
      range_max: number;           // Required
      parent_category: string;     // Required: helps LLM with context
      technologies: string[];      // Required: actual skills/requirements
      
    }
    ```
    """
    try:
        result = handle_query(
            db,
            GetOrGenerateWarning(
                persona_id=payload.persona_id,
                entity_type=payload.entity_type,
                entity_name=payload.entity_name,
                violation_type=payload.violation_type,
                entity_data=payload.entity_data
            )
        )
        return GetWarningResponse.model_validate(result)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/warnings/query", response_model=GetWarningResponse, summary="Get specific warning message")
async def get_persona_warning(
    persona_id: str,
    entity_type: str,
    entity_name: str,
    violation_type: str,
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Fetch specific warning message for a violated entity.
    
    **When to call**: Every time a weight crosses the min/max threshold.
    
    **Parameters**:
    - **persona_id**: The preview ID returned from /warnings/generate (e.g., "preview-a1b2c3d4")
    - **entity_type**: "category" or "subcategory"
    - **entity_name**: Exact name (e.g., "Technical Skills", "Python Programming")
    - **violation_type**: "below_min" or "above_max"
    
    **Returns**: The specific warning message to display to the user.
    """
    try:
        result = handle_query(
            db,
            GetWarningByEntity(
                persona_id=persona_id,
                entity_type=entity_type,
                entity_name=entity_name,
                violation_type=violation_type
            )
        )
        return GetWarningResponse.model_validate(result)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/warnings/{persona_id}", response_model=list[PersonaWarningRead], summary="List all warnings")
async def list_persona_warnings(
    persona_id: str,
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    List all warning messages for a persona (preview or saved).
    
    **Use case**: 
    - Debugging
    - Showing all potential warnings upfront
    - Admin dashboard
    """
    warnings = handle_query(db, ListWarningsByPersona(persona_id=persona_id))
    return [PersonaWarningRead.model_validate(w) for w in warnings]


@router.post("/warnings/link", response_model=LinkWarningsResponse, summary="Link warnings to saved persona")
async def link_warnings_to_persona(
    payload: LinkWarningsRequest,
    db: Session = Depends(db_session),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Link preview warnings to a saved persona.
    
    **When to call**: Immediately after successfully saving a persona via POST /personas
    
    **Flow**:
    1. User generates warnings → gets preview-xxx ID
    2. User saves persona → gets real persona ID
    3. Frontend calls this endpoint to link them
    
    **Example**:
```javascript
    // After persona save
    const savedPersona = await savePersona(data);
    await linkWarnings({
        temp_persona_id: "preview-a1b2c3d4",
        saved_persona_id: savedPersona.id
    });
```
    """
    result = handle_command(
        db,
        LinkWarningsToPersona(
            temp_persona_id=payload.temp_persona_id,
            saved_persona_id=payload.saved_persona_id
        )
    )
    return LinkWarningsResponse.model_validate(result)