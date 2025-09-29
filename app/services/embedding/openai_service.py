from typing import List, Dict, Any
from openai import AsyncOpenAI
from .base import EmbeddingService

class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI embedding implementation"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.dimension = 1536 if "small" in model else 3072
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            'provider': 'openai',
            'model': self.model,
            'dimension': self.dimension
        }