from typing import Dict, Any
from openai import AsyncOpenAI
import json
import re
from .prompts import PersonaPrompts


class PersonaSelfValidator:
    """Phase 5: LLM validates its own output"""
    
    def __init__(self, client: AsyncOpenAI, model: str):
        self.client = client
        self.model = model
        self.supports_json_mode = model in ["gpt-4o", "gpt-4-turbo-preview", "gpt-3.5-turbo-1106","gpt-4o-mini"]
    
    async def validate_and_correct(
        self,
        persona: Dict,
        analysis: Dict,
        jd_text: str,
        weight_calculator
    ) -> Dict[str, Any]:
        """
        Validate persona against original analysis.
        Returns corrected persona if issues found.
        """
        try:
            prompt = PersonaPrompts.self_validation_prompt(persona, analysis, jd_text)
            
            messages = [
                {"role": "system", "content": "You validate personas against JD requirements."},
                {"role": "user", "content": prompt}
            ]
            
            call_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1
            }
            
            if self.supports_json_mode:
                call_params["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**call_params)
            validation_result = self._extract_json(response.choices[0].message.content)
            
            if not validation_result.get('is_valid', True):
                print(f"⚠️  Validation found issues: {validation_result.get('issues', [])}")
                print(f"💡 Reasoning: {validation_result.get('reasoning', 'N/A')}")
                
                # Apply recommendations if they exist
                recommendations = validation_result.get('recommendations', {})
                if recommendations:
                    print("🔧 Applying corrections...")
                    persona = self._apply_corrections(persona, recommendations, weight_calculator)
            else:
                print("✅ Self-validation passed!")
            
            return persona
            
        except Exception as e:
            print(f"⚠️  Self-validation failed: {str(e)}")
            # Continue without validation - return original persona
            return persona
    
    def _apply_corrections(self, persona: Dict, recommendations: Dict, weight_calculator) -> Dict:
        """Apply LLM's correction recommendations"""
        
        name_to_key = {
            'Technical Skills': 'technical',
            'Cognitive Demands': 'cognitive',
            'Values (Schwartz)': 'values',
            'Foundational Behaviors': 'behavioral',
            'Leadership Skills': 'leadership',
            'Education and Experience': 'education_experience'
        }
        
        # Apply recommended changes
        for cat_name, new_weight in recommendations.items():
            cat = next((c for c in persona['categories'] if c['name'] == cat_name), None)
            if cat:
                old_weight = cat['weight_percentage']
                new_weight_int = int(round(new_weight))
                
                # Only if significant change (>5%)
                if abs(new_weight_int - old_weight) > 5:
                    cat['weight_percentage'] = new_weight_int
                    print(f"   {cat_name}: {old_weight}% → {new_weight_int}%")
        
        # Re-normalize to ensure sum = 100
        weights_dict = {}
        for cat in persona['categories']:
            cat_name = cat['name']
            if cat_name in name_to_key:
                weights_dict[name_to_key[cat_name]] = cat['weight_percentage']
        
        normalized = weight_calculator._normalize_weights(weights_dict)
        
        # Apply normalized weights back
        for cat in persona['categories']:
            cat_name = cat['name']
            if cat_name in name_to_key:
                internal_key = name_to_key[cat_name]
                cat['weight_percentage'] = normalized[internal_key]
                
                # Update ranges
                new_range = self._calculate_range(normalized[internal_key])
                cat['range_min'] = new_range[0]
                cat['range_max'] = new_range[1]
        
        return persona
    
    def _calculate_range(self, weight: int) -> tuple:
        """Calculate range_min and range_max based on weight"""
        range_min = -min(5, max(2, weight // 7))
        range_max = min(10, max(3, weight // 3.5))
        return (range_min, range_max)
    
    def _extract_json(self, content: str) -> Dict:
        """Extract JSON from LLM response"""
        try:
            return json.loads(content)
        except:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError("Could not extract JSON from response")