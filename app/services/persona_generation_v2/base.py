from abc import ABC, abstractmethod
from typing import Dict, Any

class PersonaGeneratorService2(ABC):
    """Abstract interface for AI-powered persona generation"""
    
    @abstractmethod
    async def generate_persona_from_jd(self, jd_text: str, jd_id: str) -> Dict[str, Any]:
        """
        Generate complete persona structure from JD text.
        
        Args:
            jd_text: Job description text
            jd_id: Job description ID
            
        Returns:
            Dict matching PersonaCreate schema
        """
        pass