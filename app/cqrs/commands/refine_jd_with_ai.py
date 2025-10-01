from dataclasses import dataclass
from app.cqrs.commands.base import Command
from typing import Optional
@dataclass
class RefineJDWithAI(Command):
    """Command to refine JD using AI"""
    jd_id: str
    role: str
    company_id: Optional[str] = None
    methodology: str = "direct"
    min_similarity: float = 0.5