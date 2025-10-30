from typing import Dict, Any
import json
import re
from .prompts import PersonaPrompts
from app.services.llm.OpenAIClient import OpenAIClient


class PersonaWarningGenerator:
    """Generate warning messages for weight violations using LLM"""
    
    def __init__(self, client: OpenAIClient, model: str):
        self.client = client
        self.model = model
        self.supports_json_mode = model in ["gpt-4o", "gpt-4-turbo-preview", "gpt-3.5-turbo-1106", "gpt-4o-mini"]
    
    async def generate_all_warnings(
        self,
        persona_data: Dict,
        jd_analysis: Dict = None
    ) -> Dict[str, Any]:
        """
        Generate warning messages for all categories and subcategories.
        
        Args:
            persona_data: Full persona structure (PersonaCreate format)
            jd_analysis: Optional JD analysis for context (not used currently)
            
        Returns:
            Dict with warnings list
        """
        try:
            prompt = PersonaPrompts.warning_generation_prompt(persona_data, jd_analysis)
            
            messages = [
                {"role": "system", "content": "You generate contextual warning messages for persona weight violations."},
                {"role": "user", "content": prompt}
            ]
            
            call_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 6000  # ✅ Increase token limit for large responses
            }
            
            if self.supports_json_mode:
                call_params["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat_completion(**call_params)
            warnings_json = response.choices[0].message.content
            
            # ✅ Add debug logging
            print(f"📝 LLM Response length: {len(warnings_json)} characters")
            
            return self._extract_json(warnings_json)
            
        except json.JSONDecodeError as e:
            # ✅ Better error message with context
            print(f"❌ JSON Parse Error at line {e.lineno}, column {e.colno}")
            print(f"📄 Response snippet around error:\n{warnings_json[max(0, e.pos-200):e.pos+200]}")
            raise ValueError(f"LLM returned invalid JSON. Error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error generating warnings: {str(e)}")
    async def generate_single_warning(
        self,
        entity_type: str,
        entity_data: Dict
    ) -> Dict[str, Any]:
        """
        Generate warning for a SINGLE entity only.
        
        Args:
            entity_type: "category" or "subcategory"
            entity_data: {name, weight, range_min, range_max, technologies, parent_category}
        
        Returns:
            Dict with below_min_message and above_max_message
        """
        try:
            prompt = PersonaPrompts.single_entity_warning_prompt(entity_type, entity_data)
            
            messages = [
                {"role": "system", "content": "You generate concise warning messages for persona weight violations."},
                {"role": "user", "content": prompt}
            ]
            
            call_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            if self.supports_json_mode:
                call_params["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat_completion(**call_params)
            warning_json = response.choices[0].message.content
            
            return self._extract_json(warning_json)
            
        except Exception as e:
            raise ValueError(f"Error generating single entity warning: {str(e)}")
    
    def _extract_json(self, content: str) -> Dict:
        """Extract JSON from LLM response with better error handling"""
        # Remove markdown code blocks if present
        content = re.sub(r'^```json\s*', '', content.strip())
        content = re.sub(r'\s*```$', '', content.strip())
        
        try:
            # Try direct parsing first
            return json.loads(content)
        except json.JSONDecodeError as e:
            # Try to find JSON object in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # ✅ Try to fix common issues
            # Fix trailing commas
            content_fixed = re.sub(r',(\s*[}\]])', r'\1', content)
            try:
                return json.loads(content_fixed)
            except json.JSONDecodeError:
                pass
            
            # If all else fails, raise with helpful context
            raise ValueError(
                f"Could not extract valid JSON from LLM response. "
                f"Response length: {len(content)} chars. "
                f"First 500 chars: {content[:500]}"
            )