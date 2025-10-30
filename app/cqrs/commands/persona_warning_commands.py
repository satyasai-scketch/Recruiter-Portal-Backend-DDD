from dataclasses import dataclass
from typing import Dict
from .base import Command


@dataclass
class GeneratePersonaWarnings(Command):
    """Command to generate all warning messages for a persona"""
    persona_data: Dict

@dataclass
class GenerateSingleEntityWarning(Command):
    """Command to generate warning for single entity on-demand"""
    persona_id: str
    entity_type: str
    entity_name: str
    entity_data: Dict
@dataclass
class LinkWarningsToPersona(Command):
    """Command to link preview warnings to saved persona"""
    temp_persona_id: str
    saved_persona_id: str