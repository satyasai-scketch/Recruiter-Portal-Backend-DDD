# Command: UploadCVFile

from .base import Command


class UploadCVFile(Command):
	"""Command to upload a single CV file with deduplication and versioning."""
	
	def __init__(self, file_bytes: bytes, filename: str, candidate_info: dict = None, user_id: str = None):
		self.file_bytes = file_bytes
		self.filename = filename
		self.candidate_info = candidate_info or {}
		self.user_id = user_id
