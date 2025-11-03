from typing import Dict, Any
import json
import re
from .prompts import PersonaPrompts
from app.services.llm.OpenAIClient import OpenAIClient


class PersonaAnalyzer:
    """Phase 1: Deep JD analysis using LLM"""
    
    def __init__(self, client: OpenAIClient, model: str):
        self.client = client
        self.model = model
        self.supports_json_mode = model in ["gpt-4o", "gpt-4-turbo-preview", "gpt-3.5-turbo-1106","gpt-4o-mini"]
    
    async def analyze_jd(self, jd_text: str) -> Dict[str, Any]:
        """Analyze JD and extract structured intelligence"""
        try:
            prompt = PersonaPrompts.jd_analysis_prompt(jd_text)
            
            messages = [
                {"role": "system", "content": "You are an expert at deeply understanding job requirements."},
                {"role": "user", "content": prompt}
            ]
            
            call_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3
            }
            
            if self.supports_json_mode:
                call_params["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat_completion(**call_params)
            analysis_json = response.choices[0].message.content
            
            return self._extract_json(analysis_json)
            
        except Exception as e:
            raise ValueError(f"Error in JD analysis: {str(e)}")
    
    def _extract_json(self, content: str) -> Dict:
        """Extract JSON from LLM response"""
        try:
            return json.loads(content)
        except:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError("Could not extract JSON from response")