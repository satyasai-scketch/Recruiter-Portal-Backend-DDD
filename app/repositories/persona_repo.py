from typing import Optional

from app.db.session import get_session
from app.db.models.persona import PersonaModel


class PersonaRepository:
	"""Data access for personas (placeholder)."""

	def __init__(self):
		self.session = get_session()

	def get(self, persona_id: str) -> Optional[PersonaModel]:
		return None

	def create(self, persona: PersonaModel) -> PersonaModel:
		return persona
