# Job Description Commands

from .base import Command


class CreateJobDescription(Command):
	"""Command to create a new job description."""
	
	def __init__(self, payload: dict):
		self.payload = payload


class ApplyJDRefinement(Command):
	"""Command to apply AI-refined text to a job description."""
	
	def __init__(self, jd_id: str, refined_text: str):
		self.jd_id = jd_id
		self.refined_text = refined_text


class UpdateJobDescription(Command):
	"""Command to update job description fields."""
	
	def __init__(self, jd_id: str, fields: dict, updated_by: str = None):
		self.jd_id = jd_id
		self.fields = fields
		self.updated_by = updated_by


class DeleteJobDescription(Command):
	"""Command to delete a job description and all associated data."""
	
	def __init__(self, jd_id: str):
		self.jd_id = jd_id