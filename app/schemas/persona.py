from pydantic import BaseModel
from typing import Dict


class WeightIntervalSchema(BaseModel):
	min: float
	max: float


class PersonaCreate(BaseModel):
	job_description_id: str
	name: str
	weights: Dict[str, float]
	intervals: Dict[str, WeightIntervalSchema] = {}


class PersonaRead(BaseModel):
	id: str
	job_description_id: str
	name: str
	weights: Dict[str, float]
	intervals: Dict[str, WeightIntervalSchema]
