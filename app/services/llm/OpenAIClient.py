from typing import List, Dict, Any
from openai import AsyncOpenAI
from .base import LLMChatClient
from langsmith.wrappers import wrap_openai

class OpenAIClient(LLMChatClient):
    """OpenAI chat client implementation"""
    
    def __init__(self, api_key: str):
        self.client = wrap_openai(AsyncOpenAI(api_key=api_key))
        #self.model = model
    
    async def chat_completion(self, messages: List[Dict[str, Any]],model: str = "gpt-4o-mini", temperature: float = 0.7, max_tokens: int = 2000,response_format: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a chat completion"""
        response = await self.client.chat.completions.create(model=model, messages=messages, temperature= temperature, max_tokens=max_tokens,response_format=response_format)
        return response

    def get_model_info(self) -> Dict[str, Any]:
        return {
            'provider': 'openai',
            'model': self.model,
        }