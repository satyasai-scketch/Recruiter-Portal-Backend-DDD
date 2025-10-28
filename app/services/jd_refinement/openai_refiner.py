from typing import Dict, Any, List
import json
from openai import AsyncOpenAI
from .base import AIRefinerService
from .prompt_templates import JDPromptTemplates
from app.services.llm.OpenAIClient import OpenAIClient

class OpenAIRefinerService(AIRefinerService):
    """OpenAI implementation for JD refinement"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7
    ):
        self.client = OpenAIClient(api_key,model)
        # self.model = model
        self.temperature = temperature
    
    async def refine_with_prompt(self, prompt: str) -> str:
        """Send prompt to OpenAI and get refined JD"""
        try:
            response = await self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR consultant specializing in writing compelling, professional job descriptions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=2000
            )
            
            refined_jd = response.choices[0].message.content.strip()
            return refined_jd
            
        except Exception as e:
            print(f"Error in AI refinement: {e}")
            raise
    
    async def extract_improvements(self, original: str, refined: str) -> List[str]:
        """Extract improvements made during refinement"""
        try:
            prompt = JDPromptTemplates.extract_improvements_prompt(original, refined)
            
            response = await self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing job description improvements. Always respond with valid JSON arrays."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse JSON response
            improvements = json.loads(result)
            
            if isinstance(improvements, list):
                return improvements
            else:
                return ["Improvements extracted but format unexpected"]
                
        except json.JSONDecodeError:
            return ["Enhanced structure and clarity", "Added missing sections", "Improved professional tone"]
        except Exception as e:
            print(f"Error extracting improvements: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        response = self.client.get_model_info()
        response["temperature"]  = self.temperature
        return response