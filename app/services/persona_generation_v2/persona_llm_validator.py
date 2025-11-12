from typing import Dict, Any, List
import json
import re

from app.services.llm.OpenAIClient import OpenAIClient
from .prompts2 import PersonaPrompts2

class PersonaLLMValidator:
    """Phase 4: Pure LLM validation with intelligent corrections"""

    def __init__(self, client: OpenAIClient, model: str):
        self.client = client
        self.model = model
        self.supports_json_mode = model in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo-preview"]

    async def validate_and_correct(
        self,
        persona: Dict,
        analysis: Dict,
        jd_text: str,
        original_weights: Dict
    ) -> Dict[str, Any]:
        """
        Validate persona and correct if needed using pure LLM reasoning.
        """
        try:
            # First check basic structural validity
            validation_issues = self._check_structure(persona)

            if validation_issues:
                print(f"⚠️  Structural issues found: {validation_issues}")
                # Ask LLM to fix structural issues
                persona = await self._fix_structure(persona, validation_issues)

            # Then validate semantic correctness
            prompt = PersonaPrompts2.build_validation_prompt(
                persona, analysis, jd_text, original_weights
            )

            messages = [
                {
                    "role": "system",
                    "content": "You validate and correct candidate personas to ensure alignment with job requirements."
                },
                {"role": "user", "content": prompt}
            ]

            call_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.0
            }

            #if self.supports_json_mode:
            call_params["response_format"] = {"type": "json_object"}

            response = await self.client.chat_completion(**call_params)
            validation_result = self._extract_json(response.choices[0].message.content)

            if not validation_result.get('is_valid', True):
                print(f"⚠️  Validation found issues:")
                for issue in validation_result.get('issues', []):
                    print(f"   - {issue}")
                print(f"💡 Reasoning: {validation_result.get('reasoning', 'N/A')}")

                # Apply LLM corrections
                corrections = validation_result.get('corrections', {})
                if corrections:
                    print("🔧 Applying LLM corrections...")
                    persona = self._apply_corrections(persona, corrections)
            else:
                print("✅ Validation passed!")

            return persona

        except Exception as e:
            print(f"⚠️  Validation failed: {str(e)}")
            return persona  # Return original if validation fails

    def _check_structure(self, persona: Dict) -> List[str]:
        """Check basic structural requirements"""
        issues = []

        if 'categories' not in persona:
            issues.append("Missing categories key")
            return issues

        categories = persona['categories']

        # Check sum of main categories
        main_sum = sum(c.get('weight_percentage', 0) for c in categories)
        if abs(main_sum - 100) > 2:
            issues.append(f"Main categories sum to {main_sum}% (should be 100%)")

        # Check subcategory sums
        for cat in categories:
            cat_name = cat.get('name', 'Unknown')
            subcats = cat.get('subcategories', [])
            if subcats:
                subcat_sum = sum(s.get('weight_percentage', 0) for s in subcats)
                if abs(subcat_sum - 100) > 2:
                    issues.append(
                        f"{cat_name} subcategories sum to {subcat_sum}% (should be 100%)"
                    )

        return issues

    async def _fix_structure(self, persona: Dict, issues: List[str]) -> Dict:
        """Use LLM to fix structural issues"""
        prompt = f"""Fix these structural issues in the persona:

Issues:
{json.dumps(issues, indent=2)}

Current Persona:
{json.dumps(persona, indent=2)}

Return the corrected persona with:
1. Main categories summing to exactly 100%
2. Each subcategory group summing to exactly 100%
3. All other structure preserved

Use proportional adjustment - if main categories sum to 98%, scale all by 100/98.
If subcategories are off, scale them proportionally.

Return ONLY the corrected persona JSON.
"""

        messages = [
            {"role": "system", "content": "You fix structural issues in persona JSON."},
            {"role": "user", "content": prompt}
        ]

        call_params = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1
        }

        #if self.supports_json_mode:
        call_params["response_format"] = {"type": "json_object"}

        response = await self.client.chat_completion(**call_params)
        corrected = self._extract_json(response.choices[0].message.content)

        print("🔧 Structure fixed by LLM")
        return corrected

    
    def _apply_corrections(self, persona: Dict, corrections: Dict) -> Dict:
        """Apply LLM-suggested corrections to persona"""

        # Apply main category corrections
        main_corrections = corrections.get('main_categories', {})
        for cat in persona['categories']:
            cat_name = cat['name']
            if cat_name in main_corrections:
                correction = main_corrections[cat_name]
                old_weight = cat['weight_percentage']
                if isinstance(correction, dict):
                    new_weight = correction.get('weight', old_weight)
                    reason = correction.get('reason', 'No reason provided')
                elif isinstance(correction, (int, float)):
                    new_weight = int(correction)
                    reason = 'Weight adjustment'
                else:
                    print(f"   ⚠️  Unexpected correction format for {cat_name}: {correction}")
                    continue

                cat['weight_percentage'] = new_weight

                # Recalculate range
                new_range = self._calculate_range(new_weight)
                cat['range_min'] = new_range[0]
                cat['range_max'] = new_range[1]

                print(f"   {cat_name}: {old_weight}% → {new_weight}%")
                print(f"      Reason: {correction['reason']}")

        # Check if main categories sum to 100 after corrections
        main_sum = sum(cat['weight_percentage'] for cat in persona['categories'])
        if abs(main_sum - 100) > 1:
            print(f"   ⚠️  After corrections, main sum is {main_sum}%. Asking LLM to rebalance...")
            # Could recursively call validation here, but for simplicity, just normalize
            self._normalize_categories(persona['categories'])

        # Apply subcategory corrections
        subcat_corrections = corrections.get('subcategories', {})
        for cat in persona['categories']:
            cat_name = cat['name']

            # Map category name to key used in corrections
            cat_key_map = {
                'Technical Skills': 'technical',
                'Cognitive Demands': 'cognitive',
                'Values (Schwartz)': 'values',
                'Foundational Behaviors': 'behavioral',
                'Leadership Skills': 'leadership',
                'Education and Experience': 'education_experience'
            }

            cat_key = cat_key_map.get(cat_name)
            if cat_key and cat_key in subcat_corrections:
                subcat_correction_list = subcat_corrections[cat_key]

                for correction in subcat_correction_list:
                    subcat_name = correction['name']
                    new_weight = correction['weight']

                    # Find and update subcategory
                    for subcat in cat.get('subcategories', []):
                        if subcat['name'] == subcat_name:
                            old_weight = subcat['weight_percentage']
                            subcat['weight_percentage'] = new_weight

                            # Recalculate range
                            new_range = self._calculate_range(new_weight)
                            subcat['range_min'] = new_range[0]
                            subcat['range_max'] = new_range[1]

                            print(f"   {cat_name} > {subcat_name}: {old_weight}% → {new_weight}%")
                            print(f"      Reason: {correction['reason']}")

                # Check subcategory sum
                subcat_sum = sum(s['weight_percentage'] for s in cat.get('subcategories', []))
                if abs(subcat_sum - 100) > 1:
                    print(f"   ⚠️  {cat_name} subcats sum to {subcat_sum}%. Normalizing...")
                    self._normalize_list(cat['subcategories'])

        return persona

    def _normalize_categories(self, categories: List[Dict]) -> None:
        """Normalize main categories to sum to 100"""
        total = sum(cat['weight_percentage'] for cat in categories)
        if total == 0:
            return

        factor = 100 / total

        for cat in categories:
            cat['weight_percentage'] = int(round(cat['weight_percentage'] * factor))

        # Fix rounding
        current_sum = sum(cat['weight_percentage'] for cat in categories)
        diff = 100 - current_sum
        if diff != 0:
            largest = max(categories, key=lambda c: c['weight_percentage'])
            largest['weight_percentage'] += diff

        print(f"   ✅ Main categories normalized to 100%")

    def _normalize_list(self, items: List[Dict]) -> None:
        """Normalize list items to sum to 100"""
        total = sum(item['weight_percentage'] for item in items)
        if total == 0:
            return

        factor = 100 / total

        for item in items:
            item['weight_percentage'] = int(round(item['weight_percentage'] * factor))

        # Fix rounding
        current_sum = sum(item['weight_percentage'] for item in items)
        diff = 100 - current_sum
        if diff != 0:
            largest = max(items, key=lambda i: i['weight_percentage'])
            largest['weight_percentage'] += diff

    def _calculate_range(self, weight: int) -> tuple:
        """Calculate range_min and range_max based on weight"""
        range_min = -min(5, max(2, weight // 7))
        range_max = min(10, max(3, weight // 3.5))
        return (range_min, range_max)

    def _extract_json(self, content: str) -> Dict:
        """Extract JSON from LLM response"""
        content = content.strip()
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