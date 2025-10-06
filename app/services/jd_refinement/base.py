from abc import ABC, abstractmethod
from typing import Dict, Any

class AIRefinerService(ABC):
    """Abstract interface for AI-based JD refinement"""
    
    @abstractmethod
    async def refine_with_prompt(self, prompt: str) -> str:
        """
        Send prompt to AI and get refined JD.
        
        Args:
            prompt: Complete prompt with context
            
        Returns:
            Refined JD text
        """
        pass
    
    @abstractmethod
    async def extract_improvements(self, original: str, refined: str) -> list:
        """
        Extract list of improvements made.
        
        Args:
            original: Original JD text
            refined: Refined JD text
            
        Returns:
            List of improvement strings
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get AI model metadata"""
        pass