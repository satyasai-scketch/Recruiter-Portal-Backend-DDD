# app/cqrs/commands/persona_commands.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import Command

@dataclass
class CreatePersona(Command):
    """Command to create a new persona."""
    def __init__(self, payload: dict, created_by: str):
        self.payload = payload
        self.created_by = created_by

@dataclass
class DeletePersona(Command):
    """Command to delete an existing persona."""
    def __init__(self, persona_id: str):
        self.persona_id = persona_id

@dataclass
class UpdatePersona(Command):
    """Command to update an existing persona."""
    def __init__(self, persona_id: str, payload: dict, updated_by: str):
        self.persona_id = persona_id
        self.payload = payload
        self.updated_by = updated_by