# app/cqrs/commands/candidate_selection_status_commands.py
from dataclasses import dataclass
from typing import Dict, Any
from .base import Command


@dataclass
class CreateCandidateSelectionStatus(Command):
	"""Command to create a new candidate selection status."""
	def __init__(self, payload: dict):
		self.payload = payload


@dataclass
class UpdateCandidateSelectionStatus(Command):
	"""Command to update an existing candidate selection status."""
	def __init__(self, status_id: str, payload: dict):
		self.status_id = status_id
		self.payload = payload


@dataclass
class DeleteCandidateSelectionStatus(Command):
	"""Command to delete a candidate selection status."""
	def __init__(self, status_id: str):
		self.status_id = status_id

