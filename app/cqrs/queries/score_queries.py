# Query: Score Queries

from .base import Query


class GetCandidateScore(Query):
	"""Query to get a specific candidate score by ID."""
	
	def __init__(self, score_id: str):
		self.score_id = score_id


class ListCandidateScores(Query):
	"""Query to list scores for a specific candidate."""
	
	def __init__(self, candidate_id: str, skip: int = 0, limit: int = 100):
		self.candidate_id = candidate_id
		self.skip = skip
		self.limit = limit


class ListScoresForCandidatePersona(Query):
	"""Query to list scores for a candidate against a specific persona."""
	
	def __init__(self, candidate_id: str, persona_id: str, skip: int = 0, limit: int = 100):
		self.candidate_id = candidate_id
		self.persona_id = persona_id
		self.skip = skip
		self.limit = limit


class ListScoresForCVPersona(Query):
	"""Query to list scores for a specific CV against a persona."""
	
	def __init__(self, cv_id: str, persona_id: str, skip: int = 0, limit: int = 100):
		self.cv_id = cv_id
		self.persona_id = persona_id
		self.skip = skip
		self.limit = limit


class ListLatestCandidateScoresPerPersona(Query):
	"""Query to list the latest score for each persona for a candidate."""
	
	def __init__(self, candidate_id: str, skip: int = 0, limit: int = 100):
		self.candidate_id = candidate_id
		self.skip = skip
		self.limit = limit


class ListAllScores(Query):
	"""Query to list all scores with pagination."""
	
	def __init__(self, skip: int = 0, limit: int = 100):
		self.skip = skip
		self.limit = limit


class ListScoresForPersona(Query):
	"""Query to list all scores for a specific persona (across all candidates)."""
	
	def __init__(self, persona_id: str, skip: int = 0, limit: int = 100):
		self.persona_id = persona_id
		self.skip = skip
		self.limit = limit
