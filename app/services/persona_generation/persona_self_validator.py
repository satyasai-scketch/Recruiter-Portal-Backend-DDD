from typing import Dict, Any, List
import json
import re
from .prompts import PersonaPrompts
from app.services.llm.OpenAIClient import OpenAIClient


class PersonaSelfValidator:
    """Phase 5: LLM validates its own output with smart correction preservation"""
    
    def __init__(self, client: OpenAIClient, model: str):
        self.client = client
        self.model = model
        self.supports_json_mode = model in ["gpt-4o", "gpt-4-turbo-preview", "gpt-3.5-turbo-1106", "gpt-4o-mini"]
    
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
            
            response = await self.client.chat_completion(**call_params)
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
            
            # Validate subcategories as well
            persona = self._validate_all_subcategories(persona)
            
            return persona
            
        except Exception as e:
            print(f"⚠️  Self-validation failed: {str(e)}")
            # Continue without validation - return original persona
            return persona
    
    def _apply_corrections(self, persona: Dict, recommendations: Dict, weight_calculator) -> Dict:
        """
        Apply LLM's correction recommendations with smart normalization.
        
        Logic:
        1. Apply recommended corrections to main categories
        2. Track which categories were corrected
        3. If >50% categories corrected → normalize ALL
        4. If ≤50% categories corrected → lock corrections, normalize only non-corrected
        5. Use proportional rounding to fix sum = 100
        """
        
        name_to_key = {
            'Technical Skills': 'technical',
            'Cognitive Demands': 'cognitive',
            'Values (Schwartz)': 'values',
            'Foundational Behaviors': 'behavioral',
            'Leadership Skills': 'leadership',
            'Education and Experience': 'education_experience'
        }
        
        total_categories = len(persona['categories'])
        corrected_categories = []
        non_corrected_categories = []
        
        # Step 1: Apply recommended changes and track what was corrected
        for cat in persona['categories']:
            cat_name = cat['name']
            
            if cat_name in recommendations:
                old_weight = cat['weight_percentage']
                new_weight_int = int(round(recommendations[cat_name]))
                
                # Only if significant change (>5%)
                # if abs(new_weight_int - old_weight) > 0:
                cat['weight_percentage'] = new_weight_int
                corrected_categories.append(cat_name)
                print(f"   {cat_name}: {old_weight}% → {new_weight_int}%")
                # else:
                #     non_corrected_categories.append(cat_name)
            else:
                non_corrected_categories.append(cat_name)
        
        correction_ratio = len(corrected_categories) / total_categories
        print(f"📊 Correction ratio: {len(corrected_categories)}/{total_categories} ({correction_ratio*100:.1f}%)")
        
        # Step 2: Smart normalization based on correction threshold
        if correction_ratio > 0.9:
            # More than half needed correction - normalize ALL
            print("🔄 >50% corrected - normalizing ALL categories")
            self._normalize_all_categories(persona, name_to_key, weight_calculator)
        
        else:
            # ≤50% corrected - keep corrections fixed, normalize only non-corrected
            print(f"locking {corrected_categories}, normalizing {non_corrected_categories}")
            self._normalize_non_corrected_categories(
                persona, 
                corrected_categories, 
                non_corrected_categories
            )
        
        return persona
    
    def _normalize_all_categories(self, persona: Dict, name_to_key: Dict, weight_calculator) -> None:
        """Normalize all categories together (when >50% corrected)"""
        weights_dict = {}
        for cat in persona['categories']:
            cat_name = cat['name']
            if cat_name in name_to_key:
                weights_dict[name_to_key[cat_name]] = cat['weight_percentage']
        
        normalized = weight_calculator._normalize_weights(weights_dict)
        
        # Apply normalized weights to all
        for cat in persona['categories']:
            cat_name = cat['name']
            if cat_name in name_to_key:
                internal_key = name_to_key[cat_name]
                old_weight = cat['weight_percentage']
                cat['weight_percentage'] = normalized[internal_key]
                print(f"   🔄 {cat_name}: {old_weight}% → {cat['weight_percentage']}%")
                
                # Update ranges
                new_range = self._calculate_range(normalized[internal_key])
                cat['range_min'] = new_range[0]
                cat['range_max'] = new_range[1]
    
    def _normalize_non_corrected_categories(
        self, 
        persona: Dict, 
        corrected_categories: List[str], 
        non_corrected_categories: List[str]
    ) -> None:
        """
        Normalize only non-corrected categories (when ≤50% corrected).
        Keeps corrected weights locked.
        """
        target_sum = 100
        
        # Sum of corrected weights (these are LOCKED)
        corrected_sum = sum(
            cat['weight_percentage'] 
            for cat in persona['categories'] 
            if cat['name'] in corrected_categories
        )
        
        # Remaining budget for non-corrected categories
        remaining_budget = target_sum - corrected_sum
        
        # Sum of current non-corrected weights
        non_corrected_sum = sum(
            cat['weight_percentage'] 
            for cat in persona['categories'] 
            if cat['name'] in non_corrected_categories
        )
        
        # Validate we have positive budget
        if remaining_budget <= 0:
            print(f"   ⚠️  Warning: Corrected sum ({corrected_sum}%) leaves no room for other categories!")
            # Fallback: normalize all
            self._normalize_all_categories(persona, {}, lambda x: x)
            return
        
        # Scale non-corrected categories
        if non_corrected_sum > 0:
            scale_factor = remaining_budget / non_corrected_sum
            
            # Store original scaled values for proportional rounding
            scaled_values = {}
            
            for cat in persona['categories']:
                cat_name = cat['name']
                
                if cat_name in corrected_categories:
                    # Keep corrected weight as-is
                    print(f"   ✅ {cat_name}: {cat['weight_percentage']}% (locked)")
                else:
                    # Scale non-corrected weight
                    old_weight = cat['weight_percentage']
                    scaled_value = old_weight * scale_factor
                    scaled_values[cat_name] = scaled_value
                    cat['weight_percentage'] = int(round(scaled_value))
                    print(f"   🔄 {cat_name}: {old_weight}% → {cat['weight_percentage']}%")
            
            # Fix rounding using proportional method
            non_corrected_cats = [
                cat for cat in persona['categories'] 
                if cat['name'] in non_corrected_categories
            ]
            self._fix_rounding_proportional(
                non_corrected_cats, 
                remaining_budget,
                scaled_values
            )
            
            # Update ranges for all categories
            for cat in persona['categories']:
                new_range = self._calculate_range(cat['weight_percentage'])
                cat['range_min'] = new_range[0]
                cat['range_max'] = new_range[1]
    
    def _validate_all_subcategories(self, persona: Dict) -> Dict:
        """
        Validate all subcategories within each category with threshold logic.
        
        For each category:
        1. Check if subcategories sum to 100%
        2. If not, determine correction strategy:
           - If >50% subcats need correction: normalize ALL
           - If ≤50% subcats need correction: lock corrections, normalize rest
        """
        print("🔍 Validating subcategories...")
        
        for cat in persona['categories']:
            cat_name = cat['name']
            subcats = cat.get('subcategories', [])
            
            if not subcats:
                continue
            
            # Check sum
            subcat_sum = sum(sub['weight_percentage'] for sub in subcats)
            
            if subcat_sum != 100:
                print(f"   ⚠️  {cat_name} subcategories sum to {subcat_sum}% (should be 100%)")
                
                # For simplicity, we'll normalize all subcategories
                # (In a full implementation, you'd track which subcats were corrected by LLM)
                if subcat_sum > 0:
                    self._normalize_subcategories(cat_name, subcats)
                else:
                    print(f"   ❌ {cat_name} has zero-sum subcategories - skipping")
        
        return persona
    
    def _normalize_subcategories(self, cat_name: str, subcats: List[Dict]) -> None:
        """
        Normalize subcategories to sum to 100% using proportional rounding.
        
        Note: In a full implementation with subcategory-level corrections,
        you would apply the same >50% threshold logic here.
        """
        target_sum = 100
        current_sum = sum(sub['weight_percentage'] for sub in subcats)
        
        if current_sum == 0:
            return
        
        # Calculate scale factor
        scale_factor = target_sum / current_sum
        
        # Store original scaled values
        scaled_values = {}
        
        # Apply scaling
        for sub in subcats:
            old_weight = sub['weight_percentage']
            scaled_value = old_weight * scale_factor
            scaled_values[sub['name']] = scaled_value
            sub['weight_percentage'] = int(round(scaled_value))
        
        # Fix rounding with proportional method
        self._fix_rounding_proportional(subcats, target_sum, scaled_values)
        
        # Update ranges for subcategories
        for sub in subcats:
            new_range = self._calculate_range(sub['weight_percentage'])
            sub['range_min'] = new_range[0]
            sub['range_max'] = new_range[1]
        
        print(f"   ✅ {cat_name} subcategories normalized to 100%")
    
    def _fix_rounding_proportional(
        self, 
        categories: List[Dict], 
        target_sum: int,
        scaled_values: Dict[str, float]
    ) -> None:
        """
        Fix rounding errors using proportional method based on fractional remainders.
        This is the fairest mathematical approach.
        
        Args:
            categories: List of category/subcategory dicts
            target_sum: Target sum (usually 100)
            scaled_values: Dict mapping name to original scaled float values
        """
        current_sum = sum(c['weight_percentage'] for c in categories)
        difference = target_sum - current_sum
        
        if difference == 0:
            return
        
        # Calculate fractional remainders for each category
        remainders = []
        for cat in categories:
            cat_name = cat.get('name')
            if cat_name in scaled_values:
                scaled_value = scaled_values[cat_name]
                rounded_value = cat['weight_percentage']
                # Fractional part = how much we "lost" or "gained" in rounding
                fractional_part = scaled_value - rounded_value
                remainders.append({
                    'category': cat,
                    'remainder': fractional_part
                })
        
        if not remainders:
            # Fallback: if we don't have scaled values, use weight-based distribution
            if difference > 0:
                # Add to largest categories
                sorted_cats = sorted(categories, key=lambda c: c['weight_percentage'], reverse=True)
            else:
                # Subtract from largest categories (they can afford it)
                sorted_cats = sorted(categories, key=lambda c: c['weight_percentage'], reverse=True)
            
            for i in range(abs(difference)):
                if i < len(sorted_cats):
                    if difference > 0:
                        sorted_cats[i]['weight_percentage'] += 1
                    else:
                        sorted_cats[i]['weight_percentage'] -= 1
            return
        
        # Sort by fractional remainder
        if difference > 0:
            # Need to add: give to categories with largest positive remainders
            # (they "deserved" to be rounded up but were rounded down)
            sorted_remainders = sorted(remainders, key=lambda x: x['remainder'], reverse=True)
        else:
            # Need to subtract: take from categories with largest negative remainders
            # (they were rounded up but "deserved" to be rounded down)
            sorted_remainders = sorted(remainders, key=lambda x: x['remainder'])
        
        # Distribute difference one unit at a time to fairest candidates
        for i in range(abs(difference)):
            if i < len(sorted_remainders):
                cat = sorted_remainders[i]['category']
                if difference > 0:
                    cat['weight_percentage'] += 1
                    print(f"      ⚖️  Rounding adjustment: {cat['name']} +1% (remainder: {sorted_remainders[i]['remainder']:.3f})")
                else:
                    cat['weight_percentage'] -= 1
                    print(f"      ⚖️  Rounding adjustment: {cat['name']} -1% (remainder: {sorted_remainders[i]['remainder']:.3f})")
    
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

# class PersonaSelfValidator:
#     """Phase 5: LLM validates its own output"""
    
#     def __init__(self, client: OpenAIClient, model: str):
#         self.client = client
#         self.model = model
#         self.supports_json_mode = model in ["gpt-4o", "gpt-4-turbo-preview", "gpt-3.5-turbo-1106","gpt-4o-mini"]
    
#     async def validate_and_correct(
#         self,
#         persona: Dict,
#         analysis: Dict,
#         jd_text: str,
#         weight_calculator
#     ) -> Dict[str, Any]:
#         """
#         Validate persona against original analysis.
#         Returns corrected persona if issues found.
#         """
#         try:
#             prompt = PersonaPrompts.self_validation_prompt(persona, analysis, jd_text)
            
#             messages = [
#                 {"role": "system", "content": "You validate personas against JD requirements."},
#                 {"role": "user", "content": prompt}
#             ]
            
#             call_params = {
#                 "model": self.model,
#                 "messages": messages,
#                 "temperature": 0.1
#             }
            
#             if self.supports_json_mode:
#                 call_params["response_format"] = {"type": "json_object"}
            
#             response = await self.client.chat_completion(**call_params)
#             validation_result = self._extract_json(response.choices[0].message.content)
            
#             if not validation_result.get('is_valid', True):
#                 print(f"⚠️  Validation found issues: {validation_result.get('issues', [])}")
#                 print(f"💡 Reasoning: {validation_result.get('reasoning', 'N/A')}")
                
#                 # Apply recommendations if they exist
#                 recommendations = validation_result.get('recommendations', {})
#                 if recommendations:
#                     print("🔧 Applying corrections...")
#                     persona = self._apply_corrections(persona, recommendations, weight_calculator)
#             else:
#                 print("✅ Self-validation passed!")
            
#             return persona
            
#         except Exception as e:
#             print(f"⚠️  Self-validation failed: {str(e)}")
#             # Continue without validation - return original persona
#             return persona
    
#     def _apply_corrections(self, persona: Dict, recommendations: Dict, weight_calculator) -> Dict:
#         """Apply LLM's correction recommendations"""
        
#         name_to_key = {
#             'Technical Skills': 'technical',
#             'Cognitive Demands': 'cognitive',
#             'Values (Schwartz)': 'values',
#             'Foundational Behaviors': 'behavioral',
#             'Leadership Skills': 'leadership',
#             'Education and Experience': 'education_experience'
#         }
        
#         # Apply recommended changes
#         for cat_name, new_weight in recommendations.items():
#             cat = next((c for c in persona['categories'] if c['name'] == cat_name), None)
#             if cat:
#                 old_weight = cat['weight_percentage']
#                 new_weight_int = int(round(new_weight))
                
#                 # Only if significant change (>5%)
#                 if abs(new_weight_int - old_weight) > 5:
#                     cat['weight_percentage'] = new_weight_int
#                     print(f"   {cat_name}: {old_weight}% → {new_weight_int}%")
        
#         # Re-normalize to ensure sum = 100
#         weights_dict = {}
#         for cat in persona['categories']:
#             cat_name = cat['name']
#             if cat_name in name_to_key:
#                 weights_dict[name_to_key[cat_name]] = cat['weight_percentage']
        
#         normalized = weight_calculator._normalize_weights(weights_dict)
        
#         # Apply normalized weights back
#         for cat in persona['categories']:
#             cat_name = cat['name']
#             if cat_name in name_to_key:
#                 internal_key = name_to_key[cat_name]
#                 cat['weight_percentage'] = normalized[internal_key]
                
#                 # Update ranges
#                 new_range = self._calculate_range(normalized[internal_key])
#                 cat['range_min'] = new_range[0]
#                 cat['range_max'] = new_range[1]
        
#         return persona
    
#     def _calculate_range(self, weight: int) -> tuple:
#         """Calculate range_min and range_max based on weight"""
#         range_min = -min(5, max(2, weight // 7))
#         range_max = min(10, max(3, weight // 3.5))
#         return (range_min, range_max)
    
#     def _extract_json(self, content: str) -> Dict:
#         """Extract JSON from LLM response"""
#         try:
#             return json.loads(content)
#         except:
#             json_match = re.search(r'\{.*\}', content, re.DOTALL)
#             if json_match:
#                 return json.loads(json_match.group(0))
#             raise ValueError("Could not extract JSON from response")