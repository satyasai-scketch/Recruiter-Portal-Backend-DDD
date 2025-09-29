from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStorageService(ABC):
    """Abstract interface for vector storage operations"""
    
    @abstractmethod
    async def store_vector(self, doc_id: str, vector: List[float], 
                          metadata: Dict, content: Dict) -> bool:
        """Store vector and complete document"""
        pass
    
    @abstractmethod
    async def search_similar(self, query_vector: List[float], 
                           top_k: int = 5, min_score: float = 0.7,
                           filters: Optional[Dict] = None) -> List[Dict]:
        """Find similar vectors"""
        pass
    
    @abstractmethod
    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve complete document by ID"""
        pass
    
    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document"""
        pass