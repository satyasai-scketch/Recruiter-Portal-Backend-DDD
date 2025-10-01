# Query: GetPersona

from .base import Query


class GetPersona(Query):
	"""Query to retrieve a specific persona by ID."""
	
	def __init__(self, persona_id: str):
		self.persona_id = persona_id
