from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMChatClient(ABC):
    """Abstract interface for LLM chat clients"""
    
    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a chat completion"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get LLM model metadata"""
        pass    