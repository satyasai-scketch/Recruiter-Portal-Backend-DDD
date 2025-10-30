from typing import Dict, Any
from openai import AsyncOpenAI
import json
import re
from .prompts import PersonaPrompts
from app.services.llm.OpenAIClient import OpenAIClient


class PersonaStructureBuilder:
    """Phase 3: Build structured persona with LLM"""
    
    def __init__(self, client: OpenAIClient, model: str):
        self.client = client
        self.model = model
        self.supports_json_mode = model in ["gpt-4o", "gpt-4-turbo-preview", "gpt-3.5-turbo-1106","gpt-4o-mini"]
    
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
            
            response = await self.client.chat_completion(**call_params)
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
            
        except json.JSONDecodeError as e:
            # ✅ Better error context
            print(f"❌ JSON Parse Error at line {e.lineno}, column {e.colno}, position {e.pos}")
            print(f"📄 Response snippet around error:")
            print(persona_json[max(0, e.pos-300):min(len(persona_json), e.pos+300)])
            raise ValueError(f"LLM returned invalid JSON at position {e.pos}. Error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error generating persona structure: {str(e)}")
    
    def _extract_json(self, content: str) -> Dict:
        """Extract JSON from LLM response with comprehensive error handling"""
        
        original_content = content  # Keep for debugging
        
        # Step 1: Clean content
        content = content.strip()
        
        # Remove markdown code blocks
        content = re.sub(r'^```(?:json)?\s*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content)
        content = content.strip()
        
        # Step 2: Try direct parsing
        try:
            parsed = json.loads(content)
            print("✅ Direct JSON parsing successful")
            return parsed
        except json.JSONDecodeError as e:
            print(f"⚠️  Direct parse failed: {e.msg} at line {e.lineno}, col {e.colno}")
        
        # Step 3: Find and extract complete JSON using brace counting
        print("🔍 Attempting brace-counting extraction...")
        try:
            start_idx = content.find('{')
            if start_idx == -1:
                raise ValueError("No opening brace found")
            
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i in range(start_idx, len(content)):
                char = content[i]
                
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        
                        if brace_count == 0:
                            json_str = content[start_idx:i+1]
                            print(f"✅ Extracted complete JSON ({len(json_str)} chars)")
                            
                            try:
                                return json.loads(json_str)
                            except json.JSONDecodeError:
                                print("⚠️  Extracted JSON invalid, applying fixes...")
                                fixed = self._apply_json_fixes(json_str)
                                return json.loads(fixed)
            
            raise ValueError(f"Unclosed braces (count: {brace_count})")
        
        except json.JSONDecodeError as e:
            # Final failure - provide detailed error
            print(f"\n{'='*80}")
            print(f"❌ JSON PARSING FAILED")
            print(f"{'='*80}")
            print(f"Error: {e.msg}")
            print(f"Position: {e.pos}, Line: {e.lineno}, Column: {e.colno}")
            print(f"\nOriginal content length: {len(original_content)}")
            print(f"First 500 chars:\n{original_content[:500]}")
            print(f"\nLast 500 chars:\n{original_content[-500:]}")
            print(f"{'='*80}\n")
            
            raise ValueError(f"Could not parse JSON: {e.msg} at position {e.pos}")

    def _apply_json_fixes(self, json_str: str) -> str:
        """Apply common JSON fixes"""
        
        # Remove trailing commas
        fixed = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Remove comments
        fixed = re.sub(r'//.*?$', '', fixed, flags=re.MULTILINE)
        fixed = re.sub(r'/\*.*?\*/', '', fixed, flags=re.DOTALL)
        
        # Fix multiple commas
        fixed = re.sub(r',\s*,+', ',', fixed)
        
        print(f"🔧 Applied JSON fixes")
        return fixed