from dataclasses import dataclass
from .base import Command

@dataclass
class GeneratePersonaFromJD(Command):
    """Command to generate persona from JD text using AI"""
    jd_id: str
    #created_by: str

@dataclass
class GeneratePersonaFromJDV3(Command):
    """Command to generate persona using V3 (with caching/adaptation)"""
    jd_id: str