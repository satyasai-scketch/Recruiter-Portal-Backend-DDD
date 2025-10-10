from typing import Dict, Any
from openai import AsyncOpenAI
import json
import re
from .prompts import PersonaPrompts


class PersonaStructureBuilder:
    """Phase 3: Build structured persona with LLM"""
    
    def __init__(self, client: AsyncOpenAI, model: str):
        self.client = client
        self.model = model
        self.supports_json_mode = model in ["gpt-4o", "gpt-4-turbo-preview", "gpt-3.5-turbo-1106"]
    
    async def build_persona(
        self,
        jd_text: str,
        jd_id: str,
        analysis: Dict,
        main_weights: Dict[str, int],
        edu_split: Dict[str, int]
    ) -> Dict[str, Any]:
        """Generate structured persona matching PersonaCreate schema"""
        try:
            prompt = PersonaPrompts.persona_structure_prompt(
                jd_text=jd_text,
                analysis=analysis,
                main_weights=main_weights,
                edu_split=edu_split,
                jd_id=jd_id
            )
            
            messages = [
                {"role": "system", "content": "You are a structured persona generator. Create precise personas from analysis data."},
                {"role": "user", "content": prompt}
            ]
            
            call_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2
            }
            
            if self.supports_json_mode:
                call_params["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**call_params)
            persona_json = response.choices[0].message.content
            
            persona = self._extract_json(persona_json)
            
            # Force correct education split
            if 'categories' in persona:
                edu_cat = next((c for c in persona['categories'] if c['name'] == 'Education and Experience'), None)
                if edu_cat and 'subcategories' in edu_cat and len(edu_cat['subcategories']) >= 3:
                    edu_cat['subcategories'][0]['weight_percentage'] = edu_split['education']
                    edu_cat['subcategories'][1]['weight_percentage'] = edu_split['experience']
                    edu_cat['subcategories'][2]['weight_percentage'] = edu_split['certifications']
            
            return persona
            
        except Exception as e:
            raise ValueError(f"Error generating persona structure: {str(e)}")
    
    def _extract_json(self, content: str) -> Dict:
        """Extract JSON from LLM response"""
        try:
            return json.loads(content)
        except:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError("Could not extract JSON from response")