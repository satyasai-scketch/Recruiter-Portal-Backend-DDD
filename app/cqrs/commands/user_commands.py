from __future__ import annotations

from typing import Dict, Any
from app.cqrs.commands.base import Command


class UpdateUser(Command):
	"""Command to update a user."""
	
	def __init__(self, user_id: str, payload: Dict[str, Any]):
		self.user_id = user_id
		self.payload = payload
