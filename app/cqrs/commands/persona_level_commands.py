# app/cqrs/commands/persona_level_commands.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import Command

@dataclass
class CreatePersonaLevel(Command):
    """Command to create a new persona level."""
    def __init__(self, payload: dict):
        self.payload = payload
        
@dataclass
class UpdatePersonaLevel(Command):
    """Command to update an existing persona level."""
    def __init__(self, persona_level_id: str, payload: dict):
        self.persona_level_id = persona_level_id
        self.payload = payload

@dataclass
class DeletePersonaLevel(Command):
    """Command to delete a persona level."""
    def __init__(self, persona_level_id: str):
        self.persona_level_id = persona_level_id