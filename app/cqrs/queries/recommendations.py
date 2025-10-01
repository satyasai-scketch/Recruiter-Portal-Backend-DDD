# Query: Recommendations

from .base import Query


class Recommendations(Query):
	"""Query to get top candidate recommendations for a persona."""
	
	def __init__(self, persona_id: str, top_k: int = 10):
		self.persona_id = persona_id
		self.top_k = top_k
