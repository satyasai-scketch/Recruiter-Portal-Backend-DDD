# Command: UploadJobDescriptionDocument

from .base import Command


class UploadJobDescriptionDocument(Command):
	"""Command to upload and process a job description document."""
	
	def __init__(self, payload: dict, file_content: bytes, filename: str):
		self.payload = payload
		self.file_content = file_content
		self.filename = filename
