from typing import Dict, Any, List
import json
import re
from app.services.llm.OpenAIClient import OpenAIClient
import asyncio
from .prompts2 import PersonaPrompts2
class PersonaStructureBuilderV2:
    """Phase 3: Build structured persona using parallel LLM calls per category"""

    def __init__(self, client: OpenAIClient, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model
        self.supports_json_mode = model in ["gpt-4o", "gpt-4-turbo-preview", "gpt-3.5-turbo-1106", "gpt-4o-mini"]

    async def build_persona(
        self,
        jd_text: str,
        jd_id: str,
        analysis: Dict,
        weights_data: Dict
    ) -> Dict[str, Any]:
        """
        Generate structured persona using parallel LLM calls (one per category).
        Significantly faster than sequential generation.
        """
        try:
            print(f"🚀 Generating 6 categories in parallel with {self.model}...")

            # Create 6 parallel tasks
            tasks = [
                self._generate_category(
                    category_name="Technical Skills",
                    category_key="technical",
                    position=1,
                    jd_text=jd_text,
                    analysis=analysis,
                    weights_data=weights_data
                ),
                self._generate_category(
                    category_name="Cognitive Demands",
                    category_key="cognitive",
                    position=2,
                    jd_text=jd_text,
                    analysis=analysis,
                    weights_data=weights_data
                ),
                self._generate_category(
                    category_name="Values (Schwartz)",
                    category_key="values",
                    position=3,
                    jd_text=jd_text,
                    analysis=analysis,
                    weights_data=weights_data
                ),
                self._generate_category(
                    category_name="Foundational Behaviors",
                    category_key="behavioral",
                    position=4,
                    jd_text=jd_text,
                    analysis=analysis,
                    weights_data=weights_data
                ),
                self._generate_category(
                    category_name="Leadership Skills",
                    category_key="leadership",
                    position=5,
                    jd_text=jd_text,
                    analysis=analysis,
                    weights_data=weights_data
                ),
                self._generate_category(
                    category_name="Education and Experience",
                    category_key="education_experience",
                    position=6,
                    jd_text=jd_text,
                    analysis=analysis,
                    weights_data=weights_data
                )
            ]

            # Execute all 6 calls in parallel
            categories = await asyncio.gather(*tasks)

            # Assemble final persona
            persona = {
                "job_description_id": jd_id,
                "name": f"{analysis['role_understanding']['title']} Persona",
                "categories": categories
            }

            print("✅ All categories generated and assembled!")
            return persona

        except Exception as e:
            raise ValueError(f"Error generating persona structure: {str(e)}")

    async def _generate_category(
        self,
        category_name: str,
        category_key: str,
        position: int,
        jd_text: str,
        analysis: Dict,
        weights_data: Dict
    ) -> Dict[str, Any]:
        """Generate a single category with its subcategories"""

        try:
            prompt = PersonaPrompts2.build_category_prompt(
                category_name=category_name,
                category_key=category_key,
                jd_text=jd_text,
                analysis=analysis,
                weights_data=weights_data
            )

            messages = [
                {
                    "role": "system",
                    "content": f"You are a structured persona generator. Create the '{category_name}' category with precise weights and subcategories."
                },
                {"role": "user", "content": prompt}
            ]

            call_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.0
            }

            if self.supports_json_mode:
                call_params["response_format"] = {"type": "json_object"}

            response = await self.client.chat_completion(**call_params)
            category_json = response.choices[0].message.content

            category = self._extract_json(category_json)

            # Ensure position is set
            category['position'] = position

            print(f"   ✓ {category_name} generated")
            return category

        except Exception as e:
            raise ValueError(f"Error generating {category_name}: {str(e)}")

    

    def _extract_json(self, content: str) -> Dict:
        """Extract JSON from LLM response"""
        content = content.strip()

        # Remove markdown code blocks
        content = re.sub(r'^```(?:json)?\s*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content, flags=re.DOTALL)
        content = content.strip()

        try:
            parsed = json.loads(content)
            return parsed
        except json.JSONDecodeError as e:
            # Try brace counting extraction
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
                            return json.loads(json_str)