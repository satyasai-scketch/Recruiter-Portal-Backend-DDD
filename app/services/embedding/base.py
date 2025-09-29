from abc import ABC, abstractmethod
from typing import List, Dict, Any

class EmbeddingService(ABC):
    """Abstract interface for text embedding services"""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get embedding model metadata"""
        pass