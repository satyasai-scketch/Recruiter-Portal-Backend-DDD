# Command: CreatePersona

from .base import Command


class CreatePersona(Command):
	"""Command to create a new persona for job description scoring."""
	
	def __init__(self, payload: dict):
		self.payload = payload
