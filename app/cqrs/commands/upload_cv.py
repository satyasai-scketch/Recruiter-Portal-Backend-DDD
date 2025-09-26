# Command: UploadCVs

from .base import Command


class UploadCVs(Command):
	"""Command to upload and process multiple CVs."""
	
	def __init__(self, payloads: list[dict]):
		self.payloads = payloads
