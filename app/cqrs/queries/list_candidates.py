# Query: ListCandidates

from .base import Query


class ListCandidates(Query):
	"""Query to list candidates, optionally filtered by persona."""
	
	def __init__(self, persona_id: str | None = None):
		self.persona_id = persona_id
