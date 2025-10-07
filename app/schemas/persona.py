from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional


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


class PersonaChangeLogSchema(BaseModel):
	entity_type: str
	entity_id: str
	field_name: str
	old_value: Optional[str] = None
	new_value: Optional[str] = None
	changed_by: str

	model_config = ConfigDict(from_attributes=True)


class PersonaSubcategorySchema(BaseModel):
	id: Optional[str] = None
	name: str
	weight_percentage: int
	range_min: Optional[float] = None
	range_max: Optional[float] = None
	level_id: Optional[str] = None
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
	skillsets: List[PersonaSkillsetSchema] = []
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

	model_config = ConfigDict(from_attributes=True)


class PersonaRead(BaseModel):
	id: str
	job_description_id: str
	name: str
	role_name: Optional[str] = None
	created_by: Optional[str] = None
	weights: Optional[Dict[str, float]] = None
	intervals: Optional[Dict[str, WeightIntervalSchema]] = None
	categories: List[PersonaCategorySchema] = []
	skillsets: List[PersonaSkillsetSchema] = []
	notes: List[PersonaNotesSchema] = []
	change_logs: List[PersonaChangeLogSchema] = []

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