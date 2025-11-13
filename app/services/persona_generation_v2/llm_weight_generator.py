import asyncio
from typing import Dict, Any, List
import json
import re
import time
from app.services.llm.OpenAIClient import OpenAIClient
from .prompts2 import PersonaPrompts2
class LLMWeightGeneratorV2:
    """Split weight generation: main categories first, then parallel subcategories"""

    def __init__(self, client: OpenAIClient, model: str = "gpt-4o"):
        self.client = client
        self.main_model = model  # Use better model for main weights
        self.subcat_model = "gpt-4o-mini"  # Use cheaper model for subcategories
        self.supports_json_mode = model in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo-preview"]

    async def generate_weights(self, jd_text: str, analysis: Dict) -> Dict[str, Any]:
        """
        Two-phase weight generation:
        1. Generate main category weights (1 call)
        2. Generate subcategory weights in parallel (6 calls)
        """
        try:
            # Phase 2.1: Generate main category weights
            start1=time.time()
            print(f"🎯 Generating main category weights with {self.main_model}...")
            main_categories = await self._generate_main_weights(jd_text, analysis)
            end1=time.time()
            print(f"Time taken for main weights: {end1-start1}")

            # Extract and remove _overall_reasoning before passing to subcategory generation
            overall_reasoning = main_categories.pop('_overall_reasoning', '')
            start2=time.time()
            # Phase 2.2: Generate subcategory weights in parallel
            print(f"🚀 Generating subcategory weights in parallel with {self.subcat_model}...")
            subcategories = await self._generate_subcategories_parallel(
                jd_text, analysis, main_categories
            )
            end2=time.time()
            print(f"Time taken for subcategories: {end2-start2}")

            weights_data = {
                "main_categories": main_categories,
                "subcategories": subcategories,
                "overall_reasoning": overall_reasoning,
                "verification": self._create_verification(main_categories, subcategories)
            }
            # print(f'weights data before normalize:{weights_data["main_categories"]}')
            # print(weights_data['subcategories'])
            # print(weights_data['overall_reasoning'])
            # print(weights_data['verification'])
            # Validate and normalize if needed
            weights_data = self._validate_and_normalize(weights_data)

            return weights_data

        except Exception as e:
            raise ValueError(f"Error generating weights: {str(e)}")

    async def _generate_main_weights(self, jd_text: str, analysis: Dict) -> Dict[str, Any]:
        """Generate only main category weights"""

        prompt = PersonaPrompts2.build_main_weights_prompt(jd_text, analysis)

        messages = [
            {
                "role": "system",
                "content": "You are an expert at determining importance weights for hiring criteria."
            },
            {"role": "user", "content": prompt}
        ]

        call_params = {
            "model": self.main_model,
            "messages": messages,
            "temperature": 0.0
        }

        if self.supports_json_mode:
              call_params["response_format"] = {"type": "json_object"}

        response = await self.client.chat_completion(**call_params)
        weights_json = response.choices[0].message.content

        main_weights = self._extract_json(weights_json)


        # Handle if LLM wrapped in 'main_categories' key
        if 'main_categories' in main_weights and isinstance(main_weights['main_categories'], dict):
            print("   ⚠️  LLM returned wrapped structure, unwrapping...")
            overall_reasoning = main_weights.get('overall_reasoning', main_weights.get('_overall_reasoning', ''))
            main_weights = main_weights['main_categories']
            if overall_reasoning:
                main_weights['_overall_reasoning'] = overall_reasoning

        # Validate structure - should have category keys at top level
        expected_keys = {'technical', 'cognitive', 'values', 'behavioral', 'leadership', 'education_experience'}
        actual_keys = set(main_weights.keys()) - {'_overall_reasoning'}

        if not expected_keys.issubset(actual_keys):
            print(f"   ⚠️  Missing keys. Expected: {expected_keys}, Got: {actual_keys}")
            print(f"   Full response: {main_weights}")
            raise ValueError(f"Missing required category keys in main weights")

        print("   ✓ Main category weights generated")
        return main_weights

    async def _generate_subcategories_parallel(
        self,
        jd_text: str,
        analysis: Dict,
        main_categories: Dict
    ) -> Dict[str, List[Dict]]:
        """Generate subcategory weights for all 6 categories in parallel"""

        # Debug: Check what we received
        #print(f"   DEBUG: Main categories structure: {list(main_categories.keys())}")

        # Safely get weights with error handling
        def get_weight(key):
            if key not in main_categories:
                raise ValueError(f"Missing category key: {key}")
            cat = main_categories[key]
            if isinstance(cat, dict):
                return cat.get('weight', 0), cat.get('reasoning', '')
            else:
                raise ValueError(f"Category {key} is not a dict: {type(cat)}")

        try:
            tech_w, tech_r = get_weight('technical')
            cog_w, cog_r = get_weight('cognitive')
            val_w, val_r = get_weight('values')
            beh_w, beh_r = get_weight('behavioral')
            lead_w, lead_r = get_weight('leadership')
            edu_w, edu_r = get_weight('education_experience')
        except Exception as e:
            print(f"   ❌ Error accessing weights: {e}")
            print(f"   Full main_categories: {main_categories}")
            raise

        tasks = [
            self._generate_subcategory_weights(
                category_key="technical",
                category_name="Technical Skills",
                jd_text=jd_text,
                analysis=analysis,
                main_weight=tech_w,
                main_reasoning=tech_r
            ),
            self._generate_subcategory_weights(
                category_key="cognitive",
                category_name="Cognitive Demands",
                jd_text=jd_text,
                analysis=analysis,
                main_weight=cog_w,
                main_reasoning=cog_r
            ),
            self._generate_subcategory_weights(
                category_key="values",
                category_name="Values (Schwartz)",
                jd_text=jd_text,
                analysis=analysis,
                main_weight=val_w,
                main_reasoning=val_r
            ),
            self._generate_subcategory_weights(
                category_key="behavioral",
                category_name="Foundational Behaviors",
                jd_text=jd_text,
                analysis=analysis,
                main_weight=beh_w,
                main_reasoning=beh_r
            ),
            self._generate_subcategory_weights(
                category_key="leadership",
                category_name="Leadership Skills",
                jd_text=jd_text,
                analysis=analysis,
                main_weight=lead_w,
                main_reasoning=lead_r
            ),
            self._generate_subcategory_weights(
                category_key="education_experience",
                category_name="Education and Experience",
                jd_text=jd_text,
                analysis=analysis,
                main_weight=edu_w,
                main_reasoning=edu_r
            )
        ]

        # Execute all 6 in parallel
        results = await asyncio.gather(*tasks)

        # Combine results
        subcategories = {
            "technical": results[0],
            "cognitive": results[1],
            "values": results[2],
            "behavioral": results[3],
            "leadership": results[4],
            "education_experience": results[5]
        }

        print("   ✓ All subcategory weights generated")
        return subcategories

    async def _generate_subcategory_weights(
        self,
        category_key: str,
        category_name: str,
        jd_text: str,
        analysis: Dict,
        main_weight: int,
        main_reasoning: str
    ) -> List[Dict]:
        """Generate subcategory weights for a single category"""

        prompt = PersonaPrompts2.build_subcategory_prompt(
            category_key, category_name, jd_text, analysis, main_weight, main_reasoning
        )

        messages = [
            {
                "role": "system",
                "content": f"You determine subcategory weights for {category_name}."
            },
            {"role": "user", "content": prompt}
        ]

        call_params = {
            "model": self.subcat_model,
            "messages": messages,
            "temperature": 0.0
        }

        #if "gpt-4o" in self.subcat_model or "gpt-3.5" in self.subcat_model:
        call_params["response_format"] = {"type": "json_object"}

        response = await self.client.chat_completion(**call_params)
        subcat_json = response.choices[0].message.content

        result = self._extract_json(subcat_json)

        # Extract the list from the result
        if "subcategories" in result:
            return result["subcategories"]
        elif isinstance(result, list):
            return result
        else:
            raise ValueError(f"Unexpected format for {category_name} subcategories")

    

    def _create_verification(self, main_categories: Dict, subcategories: Dict) -> Dict:
        """Create verification sums"""
        main_sum = sum(cat['weight'] for cat in main_categories.values() if 'weight' in cat)

        verification = {
            "main_sum": main_sum,
            "technical_subcat_sum": sum(s['weight'] for s in subcategories.get('technical', [])),
            "cognitive_subcat_sum": sum(s['weight'] for s in subcategories.get('cognitive', [])),
            "values_subcat_sum": sum(s['weight'] for s in subcategories.get('values', [])),
            "behavioral_subcat_sum": sum(s['weight'] for s in subcategories.get('behavioral', [])),
            "leadership_subcat_sum": sum(s['weight'] for s in subcategories.get('leadership', [])),
            "education_subcat_sum": sum(s['weight'] for s in subcategories.get('education_experience', []))
        }

        return verification

    def _validate_and_normalize(self, weights_data: Dict) -> Dict:
        """Validate weight sums and normalize if needed"""
        main_cats = weights_data.get('main_categories', {})
        subcats = weights_data.get('subcategories', {})

        # Filter out non-category keys (like _overall_reasoning)
        category_keys = ['technical', 'cognitive', 'values', 'behavioral', 'leadership', 'education_experience']

        # Check main categories
        main_sum = sum(
            main_cats[key]['weight']
            for key in category_keys
            if key in main_cats and isinstance(main_cats[key], dict) and 'weight' in main_cats[key]
        )

        if abs(main_sum - 100) > 0:
            print(f"⚠️  Main categories sum to {main_sum}%, normalizing...")
            self._normalize_dict(main_cats, category_keys)

        # Check each subcategory group
        for cat_key in category_keys:
            if cat_key in subcats:
                subcat_list = subcats[cat_key]
                if isinstance(subcat_list, list) and subcat_list:
                    subcat_sum = sum(sub.get('weight', 0) for sub in subcat_list)
                    if abs(subcat_sum - 100) > 0:
                        print(f"⚠️  {cat_key} subcategories sum to {subcat_sum}%, normalizing...")
                        self._normalize_list(subcat_list)

        return weights_data

    def _normalize_dict(self, weights_dict: Dict, category_keys: List[str] = None) -> None:
        """Normalize weights in dictionary to sum to 100"""
        if category_keys is None:
            category_keys = ['technical', 'cognitive', 'values', 'behavioral', 'leadership', 'education_experience']

        # Only normalize actual category entries
        valid_cats = [
            key for key in category_keys
            if key in weights_dict and isinstance(weights_dict[key], dict) and 'weight' in weights_dict[key]
        ]

        total = sum(weights_dict[key]['weight'] for key in valid_cats)
        if total == 0:
            return

        factor = 100 / total

        for key in valid_cats:
            weights_dict[key]['weight'] = int(round(weights_dict[key]['weight'] * factor))

        # Fix rounding
        current_sum = sum(weights_dict[key]['weight'] for key in valid_cats)
        diff = 100 - current_sum
        if diff != 0:
            largest_key = max(valid_cats, key=lambda k: weights_dict[k]['weight'])
            weights_dict[largest_key]['weight'] += diff

    def _normalize_list(self, weights_list: List[Dict]) -> None:
        """Normalize weights in list to sum to 100"""
        total = sum(item['weight'] for item in weights_list)
        if total == 0:
            return

        factor = 100 / total

        for item in weights_list:
            item['weight'] = int(round(item['weight'] * factor))

        current_sum = sum(item['weight'] for item in weights_list)
        diff = 100 - current_sum
        if diff != 0:
            largest_idx = max(range(len(weights_list)), key=lambda i: weights_list[i]['weight'])
            weights_list[largest_idx]['weight'] += diff

    def _extract_json(self, content: str) -> Dict:
        """Extract JSON from LLM response"""
        content = content.strip()

        # Remove markdown code blocks
        content = re.sub(r'^```(?:json)?\s*\n?', '', content)
        content = re.sub(r'\n?```\s*$', '', content, flags=re.DOTALL)
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError("Could not extract JSON from response")