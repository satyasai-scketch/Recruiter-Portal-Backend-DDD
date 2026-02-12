from typing import Dict, Any, List
import json
import re
from app.services.llm.OpenAIClient import OpenAIClient
from .prompts_adapter import PersonaAdapterPrompts

class PersonaAdapterService:
    def __init__(self, client: OpenAIClient, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model
    
    async def adapt_persona(
        self, 
        original_jd_text: str, 
        new_jd_text: str, 
        ai_persona: Dict, 
        similarity_score: float
    ) -> Dict[str, Any]:
        """Route to appropriate adaptation strategy based on similarity"""
        
        if similarity_score >= 0.97:
            print(f"   Direct return (similarity: {similarity_score:.2%})")
            return ai_persona
        elif similarity_score >= 0.85:
            print(f"   Light adaptation - skillsets/levels only (similarity: {similarity_score:.2%})")
            return await self._light_adaptation(original_jd_text, new_jd_text, ai_persona)
        elif similarity_score >= 0.70:
            print(f"   Moderate adaptation - weights + skillsets + levels (similarity: {similarity_score:.2%})")
            return await self._moderate_adaptation(original_jd_text, new_jd_text, ai_persona)
        else:
            print(f"   Thorough adaptation (similarity: {similarity_score:.2%})")
            return await self._thorough_adaptation(original_jd_text, new_jd_text, ai_persona)
    
    async def _light_adaptation(
        self, 
        original_jd: str, 
        new_jd: str, 
        ai_persona: Dict
    ) -> Dict:
        """90-99% similarity: Only modify skillsets and level_id, NO weight changes"""
        
        # Extract current skillsets and levels
        current_state = self._extract_skillsets_and_levels(ai_persona)
        #print(f'current_state:{current_state}')
        
        # ✅ Use centralized prompt
        prompt = PersonaAdapterPrompts.light_adaptation_prompt(
            original_jd, new_jd, current_state
        )
        
        
        response = await self.client.chat_completion(
            model=self.model,
            messages=[
                {
                    "role": "system", 
                    "content": "You identify minimal changes between similar job descriptions. You only suggest skillset and level changes, never weight changes."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        changes = self._extract_json(response.choices[0].message.content)
        
        # Apply changes to persona
        return self._apply_light_changes(ai_persona, changes)
    
    async def _moderate_adaptation(
        self, 
        original_jd: str, 
        new_jd: str, 
        ai_persona: Dict
    ) -> Dict:
        """85-90% similarity: Allow weight changes + skillset + level changes + add/remove subcategories"""
        
        # Extract current weights and skillsets
        current_state = self._extract_full_state(ai_persona)
        
        # ✅ Use centralized prompt
        prompt = PersonaAdapterPrompts.moderate_adaptation_prompt(
            original_jd, new_jd, current_state
        )
        
        
        response = await self.client.chat_completion(
            model="gpt-4o",  # Use better model for complex weight adjustments
            messages=[
                {
                    "role": "system",
                    "content": "You adapt candidate personas by adjusting weights, skillsets, and levels to match new job requirements while maintaining structural integrity."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        changes = self._extract_json(response.choices[0].message.content)
        
        # Apply changes to persona
        return self._apply_moderate_changes(ai_persona, changes)
    
    async def _thorough_adaptation(
        self, 
        original_jd: str, 
        new_jd: str, 
        ai_persona: Dict
    ) -> Dict:
        """<85% similarity: Comprehensive adaptation (keep existing implementation)"""
        prompt = PersonaAdapterPrompts.thorough_adaptation_prompt(
            original_jd, new_jd, ai_persona
        )
        
        response = await self.client.chat_completion(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You thoroughly adapt personas for different JDs."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        return self._extract_json(response.choices[0].message.content)
    
    def _extract_skillsets_and_levels(self, persona: Dict) -> Dict:
        """Extract current skillsets and levels for light adaptation"""
        state = {}
        
        for cat in persona.get('categories', []):
            cat_name = cat['name']
            state[cat_name] = {}
            
            for subcat in cat.get('subcategories', []):
                subcat_name = subcat['name']
                skillset = subcat.get('skillset', {})
                
                state[cat_name][subcat_name] = {
                    "level_id": subcat.get('level_id'),
                    "technologies": skillset.get('technologies', [])
                }
        
        return state
    
    def _extract_full_state(self, persona: Dict) -> Dict:
        """Extract weights, skillsets, and levels for moderate adaptation"""
        main_weights = {}
        subcategories = {}
        
        for cat in persona.get('categories', []):
            cat_name = cat['name']
            main_weights[cat_name] = cat['weight_percentage']
            
            subcategories[cat_name] = []
            for subcat in cat.get('subcategories', []):
                skillset = subcat.get('skillset', {})
                subcategories[cat_name].append({
                    "name": subcat['name'],
                    "weight_percentage": subcat['weight_percentage'],
                    "level_id": subcat.get('level_id'),
                    "technologies": skillset.get('technologies', [])
                })
        
        return {
            "main_weights": main_weights,
            "subcategories": subcategories
        }
    
    def _apply_light_changes(self, persona: Dict, changes: Dict) -> Dict:
        """Apply skillset and level changes only (no weights)"""
        
        change_data = changes.get('changes', {})
        print(f'change_data:{changes}' )
        if not change_data:
            print("   No changes needed")
            return persona
        
        for cat in persona['categories']:
            cat_name = cat['name']
            if cat_name not in change_data:
                continue
            
            cat_changes = change_data[cat_name]
            
            for subcat in cat.get('subcategories', []):
                subcat_name = subcat['name']
                if subcat_name not in cat_changes:
                    continue
                
                subcat_changes = cat_changes[subcat_name]
                
                # Apply level_id change
                if 'level_id' in subcat_changes:
                    subcat['level_id'] = str(subcat_changes['level_id'])
                    print(f"   Updated {cat_name} > {subcat_name} level to {subcat_changes['level_id']}")
                
                # Apply technologies changes
                if 'technologies' in subcat_changes:
                    tech_changes = subcat_changes['technologies']
                    skillset = subcat.get('skillset', {})
                    current_tech = skillset.get('technologies', [])
                    if isinstance(tech_changes, list):
                        skillset['technologies'] = tech_changes
                        print(f"   Replaced {cat_name} > {subcat_name} technologies: {tech_changes}")
                    # Handle if LLM returns dict with add/remove/replace
                    elif isinstance(tech_changes, dict):
                        if 'replace' in tech_changes:
                            skillset['technologies'] = tech_changes['replace']
                            print(f"   Replaced {cat_name} > {subcat_name} technologies")
                        else:
                            # Add new technologies
                            if 'add' in tech_changes:
                                for tech in tech_changes['add']:
                                    if tech not in current_tech:
                                        current_tech.append(tech)
                                print(f"   Added to {cat_name} > {subcat_name}: {tech_changes['add']}")
                            
                            # Remove technologies
                            if 'remove' in tech_changes:
                                for tech in tech_changes['remove']:
                                    if tech in current_tech:
                                        current_tech.remove(tech)
                                print(f"   Removed from {cat_name} > {subcat_name}: {tech_changes['remove']}")
                            
                            skillset['technologies'] = current_tech
                    
                    subcat['skillset'] = skillset
        
        return persona
    
    def _apply_moderate_changes(self, persona: Dict, changes: Dict) -> Dict:
        """Apply weight, skillset, level changes, and add/remove subcategories"""
        
        # Apply main category weights
        print(f"changes:{changes}")
        main_weights = changes.get('main_category_weights', {})
        if main_weights:
            # Validate sum
            total = sum(main_weights.values())
            if abs(total - 100) > 1:
                print(f"   ⚠️ LLM returned main weights summing to {total}, normalizing...")
                # Normalize
                factor = 100 / total
                main_weights = {k: int(round(v * factor)) for k, v in main_weights.items()}
                # Fix rounding
                current_sum = sum(main_weights.values())
                if current_sum != 100:
                    largest = max(main_weights, key=main_weights.get)
                    main_weights[largest] += (100 - current_sum)
            
            for cat in persona['categories']:
                cat_name = cat['name']
                if cat_name in main_weights:
                    old_weight = cat['weight_percentage']
                    cat['weight_percentage'] = main_weights[cat_name]
                    
                    # Recalculate range
                    cat['range_min'] = -min(5, max(2, main_weights[cat_name] // 7))
                    cat['range_max'] = min(10, max(3, main_weights[cat_name] // 3.5))
                    
                    print(f"   {cat_name}: {old_weight}% → {main_weights[cat_name]}%")
        
        # Apply subcategory changes
        subcat_changes = changes.get('subcategory_changes', {})
        
        for cat in persona['categories']:
            cat_name = cat['name']
            if cat_name not in subcat_changes:
                continue
            
            cat_change = subcat_changes[cat_name]
            
            # Remove subcategories
            if 'remove' in cat_change:
                for subcat_name in cat_change['remove']:
                    cat['subcategories'] = [
                        s for s in cat['subcategories'] 
                        if s['name'] != subcat_name
                    ]
                    print(f"   Removed subcategory: {cat_name} > {subcat_name}")
            
            # Modify existing subcategories
            if 'modify' in cat_change:
                modify_data = cat_change['modify']
                
                for subcat in cat['subcategories']:
                    subcat_name = subcat['name']
                    if subcat_name not in modify_data:
                        continue
                    
                    subcat_mod = modify_data[subcat_name]
                    
                    # Apply weight
                    if 'weight_percentage' in subcat_mod:
                        new_weight = subcat_mod['weight_percentage']
                        old_weight = subcat['weight_percentage']
                        if new_weight != old_weight:  # ✅ Identity check
                            subcat['weight_percentage'] = new_weight
                            
                            print(f"   {cat_name} > {subcat_name}: {old_weight}% → {new_weight}%")
                        
                        
                    # Apply level_id
                    if 'level_id' in subcat_mod:
                        new_level = str(subcat_mod['level_id'])
                        old_level = subcat.get('level_id', '')
                        if new_level != old_level:  # ✅ Identity check
                            subcat['level_id'] = new_level
                            print(f"   Updated {cat_name} > {subcat_name} level to {new_level}")
                    
                    # Apply technologies
                    if 'technologies' in subcat_mod:
                        tech_changes = subcat_mod['technologies']
                        skillset = subcat.get('skillset', {})
                        current_tech = skillset.get('technologies', [])
                        if isinstance(tech_changes, list):
                            if tech_changes != current_tech:  # ✅ Identity check
                                skillset['technologies'] = tech_changes
                                print(f"   Updated {cat_name} > {subcat_name} technologies: {tech_changes}")
                                subcat['skillset'] = skillset
                        # Handle if LLM returns dict with add/remove/replace
                        elif isinstance(tech_changes, dict):
                            if 'replace' in tech_changes:
                                skillset['technologies'] = tech_changes['replace']
                                print(f"   Replaced {cat_name} > {subcat_name} technologies")
                            else:
                                if 'add' in tech_changes:
                                    for tech in tech_changes['add']:
                                        if tech not in current_tech:
                                            current_tech.append(tech)
                                    print(f"   Added to {cat_name} > {subcat_name}: {tech_changes['add']}")
                                
                                if 'remove' in tech_changes:
                                    for tech in tech_changes['remove']:
                                        if tech in current_tech:
                                            current_tech.remove(tech)
                                    print(f"   Removed from {cat_name} > {subcat_name}: {tech_changes['remove']}")
                                
                                skillset['technologies'] = current_tech
                        
                        subcat['skillset'] = skillset
                
                # Validate subcategory weights sum to 100
                subcat_sum = sum(s['weight_percentage'] for s in cat['subcategories'])
                if abs(subcat_sum - 100) > 1:
                    print(f"   ⚠️ {cat_name} subcats sum to {subcat_sum}%, normalizing...")
                    total = subcat_sum
                    if total > 0:
                        factor = 100 / total
                        for s in cat['subcategories']:
                            s['weight_percentage'] = int(round(s['weight_percentage'] * factor))
                        
                        # Fix rounding
                        current_sum = sum(s['weight_percentage'] for s in cat['subcategories'])
                        if current_sum != 100:
                            largest = max(cat['subcategories'], key=lambda x: x['weight_percentage'])
                            largest['weight_percentage'] += (100 - current_sum)
            
            # Add new subcategories
            if 'add' in cat_change:
                for new_subcat_data in cat_change['add']:
                    new_subcat = {
                        "name": new_subcat_data['name'],
                        "weight_percentage": new_subcat_data['weight_percentage'],
                        "range_min": -min(5, max(2, new_subcat_data['weight_percentage'] // 7)),
                        "range_max": min(10, max(3, new_subcat_data['weight_percentage'] // 3.5)),
                        "level_id": str(new_subcat_data.get('level_id', '3')),
                        "position": len(cat['subcategories']) + 1,
                        "skillset": {
                            "technologies": new_subcat_data.get('technologies', [])
                        }
                    }
                    cat['subcategories'].append(new_subcat)
                    print(f"   Added subcategory: {cat_name} > {new_subcat_data['name']} ({new_subcat_data['weight_percentage']}%)")
                
                # After adding, normalize if needed
                subcat_sum = sum(s['weight_percentage'] for s in cat['subcategories'])
                if abs(subcat_sum - 100) > 1:
                    print(f"   ⚠️ After adding, {cat_name} subcats sum to {subcat_sum}%, normalizing...")
                    total = subcat_sum
                    if total > 0:
                        factor = 100 / total
                        for s in cat['subcategories']:
                            s['weight_percentage'] = int(round(s['weight_percentage'] * factor))
                        
                        current_sum = sum(s['weight_percentage'] for s in cat['subcategories'])
                        if current_sum != 100:
                            largest = max(cat['subcategories'], key=lambda x: x['weight_percentage'])
                            largest['weight_percentage'] += (100 - current_sum)
        
        return persona
    
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
# from typing import Dict, Any
# import json, re
# from app.services.llm.OpenAIClient import OpenAIClient

# class PersonaAdapterService:
#     def __init__(self, client: OpenAIClient, model: str = "gpt-4o-mini"):
#         self.client = client
#         self.model = model
    
#     async def adapt_persona(self, original_jd_text: str, new_jd_text: str, 
#                            ai_persona: Dict, similarity_score: float) -> Dict[str, Any]:
#         if similarity_score > 0.95:
#             print(f"   Using light adaptation (similarity: {similarity_score:.2%})")
#             return await self._light_adaptation(new_jd_text, ai_persona)
#         elif similarity_score > 0.90:
#             print(f"   Using moderate adaptation (similarity: {similarity_score:.2%})")
#             return await self._moderate_adaptation(
#                 original_jd_text, new_jd_text, ai_persona
#             )
#         else:
#             print(f"   Using thorough adaptation (similarity: {similarity_score:.2%})")
#             return await self._thorough_adaptation(
#                 original_jd_text, new_jd_text, ai_persona
#             )
    
#     async def _light_adaptation(self, new_jd: str, ai_persona: Dict) -> Dict:
#         """Very similar - minimal changes"""
        
#         # Send FULL persona, not compressed
#         prompt = f"""A very similar JD needs minor persona adjustments.

# EXISTING PERSONA (full structure):
# {json.dumps(ai_persona, indent=2)}

# NEW JD:
# {new_jd[:2000]}

# TASK: 
# - Make minimal adjustments if new JD has clear differences
# - Adjust weights if needed (ensure categories sum to 100, subcategories sum to 100)
# - Update "technologies" arrays in skillsets if new skills mentioned
# - Update "level_id" if expertise level changed
# - Keep same structure, just adjust values

# Return the COMPLETE persona structure with adjustments as JSON.
# """
        
#         response = await self.client.chat_completion(
#             model=self.model,
#             messages=[
#                 {"role": "system", "content": "You adapt personas by modifying weights and skills while preserving structure."},
#                 {"role": "user", "content": prompt}
#             ],
#             response_format={"type": "json_object"},
#             temperature=0.1
#         )
        
#         return self._extract_json(response.choices[0].message.content)
    
#     async def _moderate_adaptation(
#         self, original_jd: str, new_jd: str, ai_persona: Dict
#     ) -> Dict:
#         """Moderately similar - two-stage approach"""
        
#         # Stage 1: Identify differences
#         diff_prompt = f"""Compare these two job descriptions.

#     ORIGINAL JD:
#     {original_jd[:2000]}

#     NEW JD:
#     {new_jd[:2000]}

#     Return JSON:
#     {{
#     "key_differences": [
#         "More AWS/cloud emphasis",
#         "7 years vs 5 years experience"
#     ],
#     "similar_aspects": ["Python", "FastAPI"],
#     "technical_changes": {{
#         "added": ["Kubernetes", "Microservices"],
#         "removed": ["Django"],
#         "emphasized": ["AWS", "Docker"]
#     }},
#     "weight_suggestions": {{
#         "technical": "+3",
#         "education": "+2",
#         "cognitive": "-1"
#     }}
#     }}
#     """
        
#         diff_response = await self.client.chat_completion(
#             model=self.model,
#             messages=[
#                 {"role": "system", "content": "You identify differences between JDs."},
#                 {"role": "user", "content": diff_prompt}
#             ],
#             response_format={"type": "json_object"},
#             temperature=0.0
#         )
        
#         differences = self._extract_json(diff_response.choices[0].message.content)
        
#         # Stage 2: Apply to full persona
#         adjust_prompt = f"""Adapt this persona based on detected differences.

#     EXISTING PERSONA:
#     {json.dumps(ai_persona, indent=2)}

#     DIFFERENCES:
#     {json.dumps(differences, indent=2)}

#     RULES:
#     1. Apply weight suggestions (ensure sums to 100)
#     2. In Technical Skills: update "technologies" with added/removed actual tech
#     3. In other categories: update "technologies" with descriptive phrases if needed
#     4. Adjust level_id if expertise changed
#     5. Keep same structure

#     Return COMPLETE adapted persona as JSON.
#     """
        
#         adjust_response = await self.client.chat_completion(
#             model=self.model,
#             messages=[
#                 {"role": "system", "content": "You adapt personas based on JD differences."},
#                 {"role": "user", "content": adjust_prompt}
#             ],
#             response_format={"type": "json_object"},
#             temperature=0.1
#         )
        
#         return self._extract_json(adjust_response.choices[0].message.content)


#     async def _thorough_adaptation(
#         self, original_jd: str, new_jd: str, ai_persona: Dict
#     ) -> Dict:
#         """Less similar - comprehensive adaptation"""
        
#         prompt = f"""Thoroughly adapt this persona for a related but different JD.

#     ORIGINAL JD:
#     {original_jd[:2000]}

#     NEW JD:
#     {new_jd[:2000]}

#     EXISTING PERSONA:
#     {json.dumps(ai_persona, indent=2)}

#     TASK: Comprehensive adaptation
#     - Analyze what's fundamentally different
#     - Adjust all weights appropriately (ensure sums to 100)
#     - Update Technical Skills "technologies" with actual tech from new JD
#     - Update other categories "technologies" with descriptive phrases
#     - Adjust level_id values (1-5) based on new requirements
#     - May need significant weight redistribution

#     Return COMPLETE adapted persona maintaining structure as JSON.
#     """
        
#         response = await self.client.chat_completion(
#             model="gpt-4o",  # Use better model for thorough work
#             messages=[
#                 {"role": "system", "content": "You thoroughly adapt personas for different JDs."},
#                 {"role": "user", "content": prompt}
#             ],
#             response_format={"type": "json_object"},
#             temperature=0.2
#         )
        
#         return self._extract_json(response.choices[0].message.content)
    
#     def _compress_persona(self, persona: Dict) -> str:
#         """Compress persona to lightweight format for prompts"""
        
#         categories = persona.get('categories', [])
        
#         compressed = "MAIN CATEGORIES:\n"
#         for cat in categories:
#             cat_name = cat.get('name', '')
#             cat_weight = cat.get('weight_percentage', 0)
#             compressed += f"- {cat_name}: {cat_weight}%\n"
            
#             subcats = cat.get('subcategories', [])
#             if subcats:
#                 sub_str = ", ".join([
#                     f"{s.get('name')} {s.get('weight_percentage')}%"
#                     for s in subcats
#                 ])
#                 compressed += f"  Subcats: {sub_str}\n"
        
#         return compressed
    
#     def _extract_json(self, content: str) -> Dict:
#         """Extract JSON from LLM response"""
#         content = content.strip()
#         content = re.sub(r'^```(?:json)?\s*\n?', '', content)
#         content = re.sub(r'\n?```\s*$', '', content, flags=re.DOTALL)
#         content = content.strip()
        
#         try:
#             return json.loads(content)
#         except json.JSONDecodeError:
#             json_match = re.search(r'\{.*\}', content, re.DOTALL)
#             if json_match:
#                 return json.loads(json_match.group(0))
#             raise ValueError("Could not extract JSON from response")