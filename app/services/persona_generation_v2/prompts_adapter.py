from typing import Dict
import json


class PersonaAdapterPrompts:
    """Centralized prompts for persona adaptation (V3)"""
    
    @staticmethod
    def light_adaptation_prompt(original_jd: str, new_jd: str, current_state: Dict) -> str:
        """
        90-99% similarity: Only modify skillsets and level_id, NO weight changes
        
        Args:
            original_jd: Original job description text
            new_jd: New job description text
            current_state: Current skillsets and levels extracted from persona
        """
        return f"""Compare these two very similar job descriptions and identify what needs to change in the candidate persona.

ORIGINAL JD:
{original_jd[:2000]}

NEW JD:
{new_jd[:2000]}

CURRENT PERSONA STATE:
{json.dumps(current_state, indent=2)}

TASK: Return ONLY the changes needed for skillsets and expertise levels.

RULES:
1. Return complete "technologies" array with updated content IF there are changes:
   - For Technical Skills: actual technology/tool names (e.g., ["Python", "React", "AWS"])
   - For other categories: descriptive requirement phrases (e.g., ["Data-driven decision making", "Strategic thinking"])
2. You can change "level_id" (1-5 scale where 1=Novice, 5=Expert) if expertise requirement changed
3. Return ONLY categories/subcategories that need changes
CRITICAL:
- Only make changes if there are ACTUAL requirement differences (new skills needed, different expertise level, different role scope)
- Formatting differences or word choice variations DO NOT justify changes
- Explicit requirements removed in the new JD should be treated as meaningful changes.

RETURN JSON FORMAT:
{{
  "changes": {{
    "Technical Skills": {{
      "Frontend Development": {{
        "technologies": ["Vue.js", "React", "TypeScript"],  // Direct array replaces all
        "level_id": "4"  // Only if level needs to change
      }}
    }},
    "Education and Experience": {{
      "Academic Qualification": {{
        "technologies": ["Master's degree in Computer Science"],  // Direct array replaces all
        "level_id": "4"
      }}
    }}
  }}
}}

If no changes needed for a category, don't include it.
Return empty "changes" object if nothing needs changing.
"""
    
    @staticmethod
    def moderate_adaptation_prompt(original_jd: str, new_jd: str, current_state: Dict) -> str:
        """
        85-90% similarity: Allow weight changes + skillset + level changes + add/remove subcategories
        
        Args:
            original_jd: Original job description text
            new_jd: New job description text
            current_state: Current weights, skillsets, and levels
        """
        return f"""Compare these two moderately similar job descriptions and determine what needs to change in the persona.

ORIGINAL JD:
{original_jd}

NEW JD:
{new_jd}

CURRENT PERSONA STATE:
Main Category Weights: {json.dumps(current_state['main_weights'], indent=2)}
Subcategories: {json.dumps(current_state['subcategories'], indent=2)}

LEVEL SCALE: 1=Novice, 2=Beginner, 3=Intermediate, 4=Advanced, 5=Expert
- Only make changes if there are ACTUAL requirement differences (new skills needed, different expertise level, different role scope)
- Formatting differences or word choice variations DO NOT justify changes
- Explicit requirements removed in the new JD should be treated as meaningful changes.

CRITICAL RULES:
1. If nothing needs changing, return empty objects: {{"main_category_weights": {{}}, "subcategory_changes": {{}}, "reasoning": "..."}}
2. If you include main_category_weights, you MUST have all 6 categories summing to EXACTLY 100
3. If you modify ANY subcategory weight in a category, you MUST provide ALL subcategory weights for that category summing to EXACTLY 100
4. For Technical Skills: can add/remove subcategories. For others: modify existing only
5. If you change main category weight but subcategory proportions stay the same, you can OMIT that category from subcategory_changes entirely
6. ONLY include subcategories in "modify" if their weight/level/technologies actually changed
7. Technologies format: Technical Skills = tech names ["Python", "AWS"], Others = requirement phrases ["Strategic thinking", "Team collaboration"]
8. Validate your math before returning: main categories = 100, each category's subcategories = 100

If adding subcategory in Technical Skills: ensure total with existing = 100. Example: 3 existing (35%+30%+15%=80%) + new (20%) = 100% ✓

RETURN JSON:
{{
  "main_category_weights": {{
    // Include ONLY if weights need to change
    // If included, MUST have all 6 categories summing to EXACTLY 100
    "Technical Skills": 42,
    "Cognitive Demands": 18,
    "Values (Schwartz)": 15,
    "Foundational Behaviors": 12,
    "Leadership Skills": 8,
    "Education and Experience": 5
  }},
  "subcategory_changes": {{
    // Include ONLY categories where changes needed
    "Technical Skills": {{
      "add": [  // Only if adding new subcategories
        {{"name": "DevOps", "weight_percentage": 25, "level_id": "3", "technologies": ["Docker", "Kubernetes"]}}
      ],
      "remove": ["Mobile Development"],  // Only if removing
      "modify": {{  // Only subcategories that need changes
        "Frontend Development": {{
          "weight_percentage": 35,  // Only if weight changes
          "level_id": "4",  // Only if level changes
          "technologies": ["React", "TypeScript", "Next.js"]  // Only if requirement changes. Direct array format.
        }}
      }}
    }}
  }},
  "reasoning": "Brief explanation"
}}
CRITICAL VALIDATION CHECKLIST (do this before returning):
✓ All 6 main category weights present and sum to EXACTLY 100
✓ For each category in subcategory_changes with "modify", ALL subcategories listed and weights sum to EXACTLY 100
✓ If adding new subcategory, total weight with existing ones = EXACTLY 100
✓ level_id is string "1" to "5" """
    
    @staticmethod
    def thorough_adaptation_prompt(original_jd: str, new_jd: str, ai_persona: Dict) -> str:
        """
        <85% similarity: Comprehensive adaptation
        
        Args:
            original_jd: Original job description text
            new_jd: New job description text
            ai_persona: Complete existing persona structure
        """
        return f"""Thoroughly adapt this persona for a related but different JD.

ORIGINAL JD:
{original_jd[:2000]}

NEW JD:
{new_jd[:2000]}

EXISTING PERSONA:
{json.dumps(ai_persona, indent=2)}

TASK: Comprehensive adaptation
- Analyze what's fundamentally different
- Adjust all weights appropriately (ensure sums to 100)
- Update Technical Skills "technologies" with actual tech from new JD
- Update other categories "technologies" with descriptive phrases
- Adjust level_id values (1-5) based on new requirements
- May need significant weight redistribution

Return COMPLETE adapted persona maintaining structure as JSON.
"""