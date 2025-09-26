# Job Description Queries

from .base import Query


class ListJobDescriptions(Query):
	"""Query to list job descriptions for a specific user."""
	
	def __init__(self, user_id: str):
		self.user_id = user_id


class GetJobDescription(Query):
	"""Query to retrieve a specific job description by ID."""
	
	def __init__(self, jd_id: str):
		self.jd_id = jd_id


class PrepareJDRefinementBrief(Query):
	"""Query to prepare a refinement brief for AI processing."""
	
	def __init__(self, jd_id: str, required_sections: list[str], template_text: str | None = None):
		self.jd_id = jd_id
		self.required_sections = required_sections
		self.template_text = template_text
