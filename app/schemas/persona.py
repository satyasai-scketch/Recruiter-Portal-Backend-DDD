from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional
from datetime import datetime


class WeightIntervalSchema(BaseModel):
	min: float
	max: float

	model_config = ConfigDict(from_attributes=True)


class PersonaSkillsetSchema(BaseModel):
	technologies: List[str] = []

	model_config = ConfigDict(from_attributes=True)


class PersonaNotesSchema(BaseModel):
	custom_notes: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)

class PersonaLevelSchema(BaseModel):
	id: Optional[str] = None
	name: str
	position: Optional[int] = None
	model_config = ConfigDict(from_attributes=True)


class PersonaChangeLogSchema(BaseModel):
	entity_type: str
	entity_id: str
	field_name: str
	old_value: Optional[str] = None
	new_value: Optional[str] = None
	changed_by: str

	model_config = ConfigDict(from_attributes=True)


class PersonaChangeLogRead(BaseModel):
	"""Schema for reading persona change logs with full details"""
	id: str
	persona_id: str
	entity_type: str
	entity_id: str
	field_name: str
	old_value: Optional[str] = None
	new_value: Optional[str] = None
	changed_by: Optional[str] = None
	changed_at: datetime
	changed_by_user: Optional[dict] = None  # User details if available

	model_config = ConfigDict(from_attributes=True)


class PersonaSubcategorySchema(BaseModel):
	id: Optional[str] = None
	name: str
	weight_percentage: int
	range_min: Optional[float] = None
	range_max: Optional[float] = None
	level_id: Optional[str] = None
	level: Optional[PersonaLevelSchema] = None
	position: Optional[int] = None
	skillset: Optional[PersonaSkillsetSchema] = None
	model_config = ConfigDict(from_attributes=True)


class PersonaCategorySchema(BaseModel):
	id: Optional[str] = None
	name: str
	weight_percentage: int
	range_min: Optional[float] = None
	range_max: Optional[float] = None
	position: Optional[int] = None
	subcategories: List[PersonaSubcategorySchema] = []
	notes: Optional[PersonaNotesSchema] = None

	model_config = ConfigDict(from_attributes=True)


class PersonaCreate(BaseModel):
	job_description_id: str = Field(..., examples=["jd-2025-DE-001"])
	name: str = Field(..., examples=["Data Engineer Persona"])
	# Optional legacy flat structure
	weights: Optional[Dict[str, float]] = None
	intervals: Optional[Dict[str, WeightIntervalSchema]] = None
	# New hierarchical structure
	categories: List[PersonaCategorySchema] = Field(default_factory=list)
	skillsets: List[PersonaSkillsetSchema] = Field(default_factory=list)
	notes: List[PersonaNotesSchema] = Field(default_factory=list)
	change_logs: List[PersonaChangeLogSchema] = Field(default_factory=list)
	# Persona-level notes
	persona_notes: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)


class PersonaRead(BaseModel):
	id: str
	job_description_id: str
	name: str
	role_name: Optional[str] = None
	role_id : Optional[str] = None
	created_at: datetime
	created_by: Optional[str] = None
	categories: List[PersonaCategorySchema] = []
	persona_notes: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)


# Persona Level Schemas
class PersonaLevelCreate(BaseModel):
	name: str = Field(..., examples=["Junior", "Mid-level", "Senior", "Lead"])
	position: Optional[int] = Field(None, examples=[1, 2, 3, 4])

	model_config = ConfigDict(from_attributes=True)


class PersonaLevelUpdate(BaseModel):
	name: Optional[str] = Field(None, examples=["Junior", "Mid-level", "Senior", "Lead"])
	position: Optional[int] = Field(None, examples=[1, 2, 3, 4])

	model_config = ConfigDict(from_attributes=True)


class PersonaLevelRead(BaseModel):
	id: str
	name: str
	position: Optional[int] = None

	model_config = ConfigDict(from_attributes=True)


class PersonaUpdate(BaseModel):
	"""Schema for updating persona with change tracking"""
	name: Optional[str] = None
	role_name: Optional[str] = None
	role_id: Optional[str] = None
	categories: Optional[List[PersonaCategorySchema]] = None
	persona_notes: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)


class PersonaDeletionStats(BaseModel):
	"""Schema for persona deletion statistics"""
	persona_id: str
	persona_name: str
	deleted_entities: dict
	external_references: dict
	deletion_status: dict

	model_config = ConfigDict(from_attributes=True)