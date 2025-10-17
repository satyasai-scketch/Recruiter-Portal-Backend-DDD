from abc import ABC, abstractmethod
from typing import Dict, Any


class CVScoringServiceBase(ABC):
    """Abstract interface for CV scoring"""
    
    @abstractmethod
    async def score_cv(self, cv_text: str, persona: Dict) -> Dict[str, Any]:
        """
        Score CV against persona requirements.
        
        Args:
            cv_text: Raw CV text
            persona: Persona dict (from database)
            
        Returns:
            Dict with scoring results
        """
        pass