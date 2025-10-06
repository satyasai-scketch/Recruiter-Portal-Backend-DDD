# Job Description Queries

from .base import Query


class ListJobDescriptions(Query):
	"""Query to list job descriptions for a specific user."""
	
	def __init__(self, user_id: str):
		self.user_id = user_id


class ListAllJobDescriptions(Query):
	"""Query to list all job descriptions (no user filter)."""
	
	def __init__(self):
		pass


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

class PrepareJDRefinementBrief(Query):
	"""Query to prepare a refinement brief for AI processing."""
	
	def __init__(self, jd_id: str, required_sections: list[str], template_text: str | None = None):
		self.jd_id = jd_id
		self.required_sections = required_sections
		self.template_text = template_text


# ADD THIS NEW QUERY
class GetJDDiff(Query):
	"""Query to get diff between original and refined JD."""
	
	def __init__(self, jd_id: str, diff_format: str = "table"):
		self.jd_id = jd_id
		self.diff_format = diff_format  # "table", "inline", or "simple"
