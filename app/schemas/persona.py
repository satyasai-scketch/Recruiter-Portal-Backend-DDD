from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional


class WeightIntervalSchema(BaseModel):
	min: float
	max: float

	model_config = ConfigDict(from_attributes=True)


class PersonaSubcategorySchema(BaseModel):
	id: Optional[str] = None
	name: str
	weight_percentage: int
	level: Optional[str] = None

	model_config = ConfigDict(from_attributes=True)


class PersonaCategorySchema(BaseModel):
	id: Optional[str] = None
	name: str
	weight_percentage: int
	subcategories: List[PersonaSubcategorySchema] = []

	model_config = ConfigDict(from_attributes=True)


class PersonaCreate(BaseModel):
	job_description_id: str = Field(..., examples=["JD123"])
	name: str = Field(..., examples=["Data Engineer Persona"])
	# Optional legacy flat structure
	weights: Optional[Dict[str, float]] = None
	intervals: Optional[Dict[str, WeightIntervalSchema]] = None
	# New hierarchical structure
	categories: List[PersonaCategorySchema] = Field(
		default_factory=list,
		examples=[[{
			"name": "Technical Skills",
			"weight_percentage": 30,
			"subcategories": [
				{"name": "Core Technology Stack", "weight_percentage": 40, "level": "L3"},
				{"name": "Data Pipelines", "weight_percentage": 60, "level": "L4"}
			]
		}]],
	)

	model_config = ConfigDict(from_attributes=True)


class PersonaRead(BaseModel):
	id: str
	job_description_id: str
	name: str
	weights: Optional[Dict[str, float]] = None
	intervals: Optional[Dict[str, WeightIntervalSchema]] = None
	categories: List[PersonaCategorySchema] = []

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