from dataclasses import dataclass


@dataclass
class PersonaCreatedEvent:
	id: str
	job_description_id: str
	name: str


@dataclass
class PersonaUpdatedEvent:
	id: str
	job_description_id: str
	name: str
