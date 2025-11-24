from typing import Dict, Any, List
import json

class PersonaPrompts2:
    """Centralized prompts for persona generation"""
    
    @staticmethod
    def jd_analysis_prompt(jd_text: str) -> str:
        """Phase 1: JD Analysis prompt"""
        return f"""You are an expert job description analyzer. Extract deep insights from this JD.

Your task: Understand what this role REALLY needs. Don't just find keywords - understand context, emphasis, and requirements.

Return a JSON analysis with this structure:

{{
  "role_understanding": {{
    "title": "exact role title from JD",
    "primary_function": "what does this person actually do day-to-day?",
    "job_family": "engineering/data_science/product/design/qa/devops/security/sales/marketing/hr/finance/business_analysis/project_management/architecture/management/executive/other",
    "seniority_level": "junior/mid/senior/lead/principal/manager/director/vp/executive",
    "seniority_reasoning": "why this level? (years, scope, impact)"
  }},

  "technical_requirements": {{
    "has_technical_requirements": true/false,
    "technical_intensity": "none/low/medium/high/very_high",
    "skill_clusters": [
      {{
        "cluster_name": "e.g., Programming Languages",
        "skills": ["Python", "Java"],
        "emphasis": "critical/important/nice_to_have",
        "frequency_in_jd": "how many times mentioned?"
      }}
    ],
    "technical_depth_required": "beginner/intermediate/advanced/expert"
  }},

  "cognitive_requirements": {{
    "primary_cognitive_level": "understand/apply/analyze/evaluate/create",
    "cognitive_distribution": {{
      "understand": "0-100",
      "apply": "0-100",
      "analyze": "0-100",
      "evaluate": "0-100",
      "create": "0-100"
    }},
    "reasoning": "why this distribution?"
  }},

  "values_requirements": {{
    "achievement_focus": "0-100",
    "security_focus": "0-100",
    "innovation_focus": "0-100",
    "collaboration_focus": "0-100",
    "reasoning": "what values does JD emphasize?"
  }},

  "behavioral_requirements": {{
    "communication_emphasis": "0-100",
    "resilience_emphasis": "0-100",
    "decision_making_emphasis": "0-100",
    "detail_orientation_emphasis": "0-100",
    "reasoning": "what behaviors are critical?"
  }},

  "leadership_requirements": {{
    "has_leadership_component": true/false,
    "mentoring_emphasis": "0-100",
    "influence_emphasis": "0-100",
    "vision_emphasis": "0-100",
    "process_emphasis": "0-100",
    "reasoning": "what leadership is expected?"
  }},

  "education_requirements": {{
    "education_importance": "critical/important/preferred/not_mentioned",
    "specific_degrees_required": ["CS", "Engineering"] or [],
    "certifications_required": ["AWS", "PMP"] or [],
    "years_experience_required": <number or null>,
    "can_substitute_education": true/false,
    "reasoning": "how much does education/experience matter?"
  }},

  "context_signals": {{
    "customer_facing": true/false,
    "cross_functional_heavy": true/false,
    "high_autonomy": true/false,
    "fast_paced": true/false,
    "innovation_driven": true/false,
    "process_driven": true/false
  }}
}}

CRITICAL:
- Understand MEANING and CONTEXT, not just keywords
- All scores are 0-100 relative emphasis

Analyze this JD:

{jd_text}"""
    @staticmethod
    def build_main_weights_prompt(jd_text: str, analysis: Dict) -> str:
        """Build prompt for main category weights only"""

        tech_req = analysis.get('technical_requirements', {})
        cog_req = analysis.get('cognitive_requirements', {})
        val_req = analysis.get('values_requirements', {})
        beh_req = analysis.get('behavioral_requirements', {})
        lead_req = analysis.get('leadership_requirements', {})
        edu_req = analysis.get('education_requirements', {})
        role = analysis.get('role_understanding', {})
        context = analysis.get('context_signals',{})

        return f"""Generate main category weights for a candidate persona based on this job description.

JOB DESCRIPTION:
{jd_text}

ANALYSIS INSIGHTS:
Role: {role.get('title')} ({role.get('seniority_level')} level)
Job Family: {role.get('job_family')}

Technical Requirements:
- Intensity: {tech_req.get('technical_intensity')}
- Depth: {tech_req.get('technical_depth_required')}

Cognitive Requirements:
- Primary Level: {cog_req.get('primary_cognitive_level')}

Values Requirements:
- Achievement: {val_req.get('achievement_focus')}/100
- Innovation: {val_req.get('innovation_focus')}/100

Behavioral Requirements:
- Communication: {beh_req.get('communication_emphasis')}/100
- Resilience: {beh_req.get('resilience_emphasis')}/100

Leadership Requirements:
- Has Component: {lead_req.get('has_leadership_component')}
- Seniority Level: {role.get('seniority_level')}

Education Requirements:
- Importance: {edu_req.get('education_importance')}
- Years Experience: {edu_req.get('years_experience_required')}

Extra Context: {json.dumps(context, indent=2)}

---

TASK: Generate weights for 6 main categories ONLY (subcategories will be generated separately).

MAIN CATEGORIES (must sum to 100):
1. Technical Skills
2. Cognitive Demands
3. Values (Schwartz)
4. Foundational Behaviors
5. Leadership Skills
6. Education and Experience

GUIDELINES:
- Consider relative importance from JD analysis
- Balance competing demands
- Align with seniority level
- Technical intensity → Technical Skills weight
- Cognitive complexity → Cognitive Demands weight
- Leadership component + seniority → Leadership Skills weight
- No single category should exceed 60%
- All categories should be at least 3%
CRITICAL WEIGHT REQUIREMENTS:
- Weights MUST reflect precise analysis, not round to convenient numbers
- Use granular values (23%, 17%, 31%) based on actual JD emphasis

RETURN JSON:

{{
  "technical": {{
    "weight": <5-50>,
    "reasoning": "Brief explanation"
  }},
  "cognitive": {{
    "weight": <5-50>,
    "reasoning": "..."
  }},
  "values": {{
    "weight": <5-50>,
    "reasoning": "..."
  }},
  "behavioral": {{
    "weight": <5-50>,
    "reasoning": "..."
  }},
  "leadership": {{
    "weight": <5-50>,
    "reasoning": "..."
  }},
  "education_experience": {{
    "weight": <5-50>,
    "reasoning": "..."
  }},
  "_overall_reasoning": "High-level strategy for weight distribution"
}}

CRITICAL: Weights MUST sum to exactly 100.
"""
    @staticmethod
    def build_subcategory_prompt(
        category_key: str,
        category_name: str,
        jd_text: str,
        analysis: Dict,
        main_weight: int,
        main_reasoning: str
    ) -> str:
        """Build focused prompt for subcategory weights"""

        # Get category-specific subcategories
        subcats_info = PersonaPrompts2._get_subcategory_info(category_key, analysis)

        return f"""Generate subcategory weights for the "{category_name}" category.

JOB DESCRIPTION (relevant sections):
{jd_text[:4000]}

MAIN CATEGORY WEIGHT: {main_weight}%
REASONING: {main_reasoning}

{subcats_info}

---

TASK: Generate weights for subcategories that sum to exactly 100.

{PersonaPrompts2._get_subcategory_template(category_key)}

GUIDELINES:
- Use the analysis insights to determine relative importance
- Subcategories MUST sum to exactly 100%
- Consider the emphasis scores from analysis
- Provide clear reasoning for each weight
- Generate precise weights based on JD emphasis, not just round numbers
RETURN JSON:

{{
  "subcategories": [
    {{"name": "<subcategory_name>", "weight": <int>, "reasoning": "..."}},
    ...
  ]
}}
"""
    @staticmethod
    def _get_subcategory_info(category_key: str, analysis: Dict) -> str:
        """Get analysis info relevant to subcategories"""

        info_map = {
            "technical": f"""
SKILL CLUSTERS: {json.dumps(analysis['technical_requirements'].get('skill_clusters', []), indent=2)}
Technical Depth: {analysis['technical_requirements'].get('technical_depth_required')}
            """,
            "cognitive": f"""
COGNITIVE DISTRIBUTION: {json.dumps(analysis['cognitive_requirements'].get('cognitive_distribution', {}), indent=2)}
Problem Solving: {analysis['cognitive_requirements'].get('problem_solving_emphasis', 50)}/100
            """,
            "values": f"""
VALUE FOCUS SCORES:
- Achievement: {analysis['values_requirements'].get('achievement_focus')}/100
- Innovation: {analysis['values_requirements'].get('innovation_focus')}/100
- Collaboration: {analysis['values_requirements'].get('collaboration_focus')}/100
- Security: {analysis['values_requirements'].get('security_focus')}/100
            """,
            "behavioral": f"""
BEHAVIORAL EMPHASIS:
- Communication: {analysis['behavioral_requirements'].get('communication_emphasis')}/100
- Resilience: {analysis['behavioral_requirements'].get('resilience_emphasis')}/100
- Decision Making: {analysis['behavioral_requirements'].get('decision_making_emphasis')}/100
            """,
            "leadership": f"""
LEADERSHIP CONTEXT:
- Has Component: {analysis['leadership_requirements'].get('has_leadership_component')}
- Mentoring: {analysis['leadership_requirements'].get('mentoring_emphasis')}/100
- Influence: {analysis['leadership_requirements'].get('influence_emphasis')}/100
- Vision: {analysis['leadership_requirements'].get('vision_emphasis')}/100
- Seniority: {analysis['role_understanding']['seniority_level']}
            """,
            "education_experience": f"""
EDUCATION CONTEXT:
- Importance: {analysis['education_requirements'].get('education_importance')}
- Years Required: {analysis['education_requirements'].get('years_experience_required')}
- Certifications: {', '.join(analysis['education_requirements'].get('certifications_required', []))}
            """
        }

        return info_map.get(category_key, "")
    @staticmethod
    def _get_subcategory_template(category_key: str) -> str:
        """Get subcategory names for each category"""

        templates = {
            "technical": """
SUBCATEGORIES (from skill clusters in analysis):
Generate based on the skill_clusters provided above.
For each cluster, create a subcategory with name matching cluster_name.
            """,
            "cognitive": """
SUBCATEGORIES (fixed):
- Problem Solving
- Design Thinking
- Attention to Detail
            """,
            "values": """
SUBCATEGORIES (fixed):
- Creativity & Self-Direction
- Achievement
- Benevolence
- Conformity
            """,
            "behavioral": """
SUBCATEGORIES (fixed):
- Collaboration
- Adaptability
- Ownership
            """,
            "leadership": """
SUBCATEGORIES (fixed):
- Mentoring & Peer Review
- Decision Making
- Strategic Vision
            """,
            "education_experience": """
SUBCATEGORIES (fixed):
- Academic Qualification
- Years of Experience
- Certifications & Portfolio
            """
        }

        return templates.get(category_key, "")
    @staticmethod
    def build_validation_prompt(
        persona: Dict,
        analysis: Dict,
        jd_text: str,
        original_weights: Dict
    ) -> str:
        """Build validation prompt"""

        # Extract current weights from persona
        current_weights = {
            cat['name']: cat['weight_percentage']
            for cat in persona['categories']
        }

        # Extract original LLM reasoning
        main_cats = original_weights['main_categories']
        overall_reasoning = original_weights.get('overall_reasoning', '')

        return f"""Validate this generated persona against the job requirements.

ORIGINAL WEIGHT REASONING:
{overall_reasoning}

CATEGORY REASONING:
- Technical ({main_cats['technical']['weight']}%): {main_cats['technical']['reasoning']}
- Cognitive ({main_cats['cognitive']['weight']}%): {main_cats['cognitive']['reasoning']}
- Values ({main_cats['values']['weight']}%): {main_cats['values']['reasoning']}
- Behavioral ({main_cats['behavioral']['weight']}%): {main_cats['behavioral']['reasoning']}
- Leadership ({main_cats['leadership']['weight']}%): {main_cats['leadership']['reasoning']}
- Education ({main_cats['education_experience']['weight']}%): {main_cats['education_experience']['reasoning']}

CURRENT PERSONA WEIGHTS:
{json.dumps(current_weights, indent=2)}

CONTEXT FROM ANALYSIS:
Role: {analysis['role_understanding']['title']} ({analysis['role_understanding']['seniority_level']})
Technical Intensity: {analysis['technical_requirements'].get('technical_intensity')}
Primary Cognitive Level: {analysis['cognitive_requirements'].get('primary_cognitive_level')}
Has Leadership: {analysis['leadership_requirements'].get('has_leadership_component')}
Extra Context : {analysis.get('context_signals',{})}

JOB DESCRIPTION:
{jd_text[:3000]}...

VALIDATION TASKS:
1. Check if weights align with original reasoning
2. Verify weights match JD emphasis
3. Check if subcategory weights make sense
4. Identify any misalignments

Return JSON:
{{
  "is_valid": true/false,
  "issues": ["list any problems found"],
  "reasoning": "explanation of validation decision",
  "corrections": {{
    "main_categories": {{
      "Technical Skills": {{"weight": 40, "reason": "..."}},
      // Only include categories that need correction
    }},
    "subcategories": {{
      "technical": [
        {{"name": "Python", "weight": 45, "reason": "..."}}
        // Only include subcategories that need correction
      ]
    }}
  }}
}}
CORRECTION RULES (CRITICAL):
1. If you provide corrections in "main_categories", you MUST include ALL 6 categories
2. The 6 weights MUST sum to EXACTLY 100
3. If you increase one category, you MUST decrease others to compensate
4. Think: "If I add 5% here, where do I take 5% from?"
CORRECTION FORMAT REQUIREMENTS:
- Each correction MUST be an object with "weight" (int) and "reason" (string)
- Include ALL 6 main categories in corrections (even if some weights don't change)
- Do NOT use plain integers - always use {{"weight": X, "reason": "..."}}
GUIDELINES:
- Only set is_valid=false if there are meaningful misalignments
- Only provide corrections if changes would improve accuracy
- Follow correction rules if correction required
- Consider the original reasoning - don't contradict it without good reason
- Be conservative - minor variations (±5%) are acceptable
- Focus on ensuring alignment with JD, not arbitrary adjustments
"""
    @staticmethod
    def build_category_prompt(
        category_name: str,
        category_key: str,
        jd_text: str,
        analysis: Dict,
        weights_data: Dict
    ) -> str:
        """Build focused prompt for a single category"""

        main_cats = weights_data['main_categories']
        subcats = weights_data['subcategories']

        cat_weight = main_cats[category_key]['weight']
        cat_reasoning = main_cats[category_key]['reasoning']
        cat_range = PersonaPrompts2._calculate_range(cat_weight)

        subcat_list = subcats[category_key]

        # Category-specific context
        context = PersonaPrompts2._get_category_context(category_key, analysis)

        return f"""Generate the "{category_name}" category for a candidate persona.

JOB DESCRIPTION (relevant excerpts):
{jd_text[:2500]}

CATEGORY WEIGHTS (from LLM analysis):
Main Category Weight: {cat_weight}%
Reasoning: {cat_reasoning}

SUBCATEGORIES TO GENERATE:
{PersonaPrompts2._format_subcategories(subcat_list)}

CONTEXT FROM JD ANALYSIS:
{context}

RANGE DETERMINATION GUIDELINES:

Determine appropriate flexibility ranges for both main category and subcategories:

range_min (how much weight can decrease):
- Critical/must-have requirements: -2 to -3 (tight)
- Important but flexible: -4 to -5 (moderate)
- Nice-to-have/optional: -6 to -8 (flexible)

range_max (how much weight can increase):
- Already comprehensive/maxed out: +3 to +5 (limited growth)
- Room for moderate growth: +6 to +8 (moderate growth)
- High expansion potential: +8 to +12 (high growth)
---

GENERATE THIS JSON STRUCTURE:

{{
  "name": "{category_name}",
  "weight_percentage": {cat_weight},
  "range_min": <determine based on criticality>,
  "range_max": <determine based on flexibility>,
  "position": <will be set externally>,
  "subcategories": [
    {{
      "name": "<subcategory_name_from_above>",
      "weight_percentage": <use_exact_weight_from_above>,
      "range_min": <determine based on skill criticality>,
      "range_max": <determine based on growth potential>,
      "level_id": "<1-5 based on context>",
      "position": <1-N>,
      "skillset": {{
        "technologies": [// IF this is Technical Skills category: extract actual tech/tools from JD
          // IF this is ANY other category: extract descriptive requirement phrases]
      }}
    }}
  ],
  "notes": {{"custom_notes": ""}}
}}

CRITICAL RULES:
1. Use EXACT main weight: {cat_weight}%
2. Use EXACT subcategory weights from above
3. 3. Determine ranges intelligently using guidelines above (consider criticality, context, requirement type)
4. level_id MUST be string "1" to "5"
For SUBCATEGORY "technologies" array - CRITICAL DISTINCTION:

   **IF generating Technical Skills category:**
   - technologies = actual tool/framework/language names
   - Example subcategory "Python Development": ["Python", "Django", "FastAPI"]
   - Example subcategory "Cloud": ["AWS", "Azure", "Docker"]

   **IF generating ANY OTHER category (Cognitive/Values/Behavioral/Leadership/Education):**
   - technologies = descriptive phrases about requirements from JD
   - Example subcategory "Achievement": ["Exceeding sales targets", "Driving revenue growth"]
   - Example subcategory "Collaboration": ["Cross-functional teamwork", "Client relationship management"]
   - Example subcategory "Problem Solving": ["Data-driven decision making", "Strategic analysis"]
   - DO NOT put technical tools here (no Python, React, AWS, etc.)
6. Extract specific, relevant content from the JD for skillset
7. Subcategories MUST sum to exactly 100%

Return ONLY valid JSON, no markdown.
"""
    @staticmethod
    def _get_category_context(category_key: str, analysis: Dict) -> str:
        """Get relevant analysis context for each category"""

        contexts = {
            "technical": f"""
Technical Intensity: {analysis['technical_requirements'].get('technical_intensity')}
Technical Depth: {analysis['technical_requirements'].get('technical_depth_required')}
Skill Clusters: {json.dumps(analysis['technical_requirements'].get('skill_clusters', []), indent=2)}
Core Technologies: {', '.join(analysis['technical_requirements'].get('core_technologies', []))}
            """,

            "cognitive": f"""
Primary Cognitive Level: {analysis['cognitive_requirements'].get('primary_cognitive_level')}
Cognitive Distribution: {json.dumps(analysis['cognitive_requirements'].get('cognitive_distribution', {}), indent=2)}
Problem Solving Emphasis: {analysis['cognitive_requirements'].get('problem_solving_emphasis', 50)}/100
            """,

            "values": f"""
Achievement Focus: {analysis['values_requirements'].get('achievement_focus')}/100
Innovation Focus: {analysis['values_requirements'].get('innovation_focus')}/100
Collaboration Focus: {analysis['values_requirements'].get('collaboration_focus')}/100
Security Focus: {analysis['values_requirements'].get('security_focus')}/100
            """,

            "behavioral": f"""
Communication Emphasis: {analysis['behavioral_requirements'].get('communication_emphasis')}/100
Resilience Emphasis: {analysis['behavioral_requirements'].get('resilience_emphasis')}/100
Decision Making Emphasis: {analysis['behavioral_requirements'].get('decision_making_emphasis')}/100
Detail Orientation: {analysis['behavioral_requirements'].get('detail_orientation_emphasis')}/100
            """,

            "leadership": f"""
Has Leadership Component: {analysis['leadership_requirements'].get('has_leadership_component')}
Seniority Level: {analysis['role_understanding']['seniority_level']}
Mentoring Emphasis: {analysis['leadership_requirements'].get('mentoring_emphasis')}/100
Influence Emphasis: {analysis['leadership_requirements'].get('influence_emphasis')}/100
Vision Emphasis: {analysis['leadership_requirements'].get('vision_emphasis')}/100
            """,

            "education_experience": f"""
Education Importance: {analysis['education_requirements'].get('education_importance')}
Years Experience Required: {analysis['education_requirements'].get('years_experience_required')}
Certifications Required: {', '.join(analysis['education_requirements'].get('certifications_required', []))}
Degree Requirement: {analysis['education_requirements'].get('degree_requirement', 'Not specified')}
            """
        }

        return contexts.get(category_key, "")
    @staticmethod
    def _format_subcategories(subcat_list: List[Dict]) -> str:
        """Format subcategories with weights and ranges for prompt"""
        formatted = []
        for sub in subcat_list:
            weight = sub['weight']
            range_vals = PersonaPrompts2._calculate_range(weight)
            formatted.append(
                f"- {sub['name']}: {weight}% (range: {range_vals[0]} to +{range_vals[1]})\n"
                f"  Reasoning: {sub['reasoning']}"
            )
        return "\n".join(formatted)
    @staticmethod
    def _calculate_range(weight: int) -> tuple:
        """Calculate range_min and range_max based on weight"""
        range_min = -min(5, max(2, weight // 7))
        range_max = min(10, max(3, weight // 3.5))
        return (range_min, range_max)
    @staticmethod
    def warning_generation_prompt(persona_data: Dict, jd_analysis: Dict = None) -> str:
        """Generate warning messages for weight violations"""
        
        # Extract role info from persona_data itself
        persona_name = persona_data.get('name', 'this role')
        
        categories_info = []
        for cat in persona_data.get('categories', []):
            cat_info = {
                'name': cat['name'],
                'weight': cat['weight_percentage'],
                'range_min': cat.get('range_min'),
                'range_max': cat.get('range_max'),
                'subcategories': []
            }
            
            for subcat in cat.get('subcategories', []):
                cat_info['subcategories'].append({
                    'name': subcat['name'],
                    'weight': subcat['weight_percentage'],
                    'range_min': subcat.get('range_min'),
                    'range_max': subcat.get('range_max')
                })
            
            categories_info.append(cat_info)
        
        return f"""Generate warning messages for weight violations in this candidate persona: "{persona_name}"

    Persona Structure:
    {json.dumps(categories_info, indent=2)}

    For EACH category and subcategory above, generate TWO warning messages:

    1. **below_min_message**: What happens if the weight goes BELOW range_min?
    - Explain which skills/capabilities get undervalued
    - What candidate quality might suffer
    - Real-world impact on hiring

    2. **above_max_message**: What happens if the weight goes ABOVE range_max?
    - What tradeoff is being made
    - Which other areas get squeezed
    - When this might be justified (if ever)

    CRITICAL RULES:
    - Keep each message to 2-3 sentences max (concise and actionable)
    - Be specific to the category/subcategory and its weight context
    - Focus on PRACTICAL hiring impact, not theory
    - Make warnings meaningful - don't just say "it's important"
    - Infer role context from the persona structure itself (e.g., high technical weight = tech role)

    Return JSON in this exact format:
    {{
    "warnings": [
        {{
        "entity_type": "category",
        "entity_name": "Technical Skills",
        "below_min_message": "Reducing Technical Skills below this much may result in hiring candidates who lack depth in core technical areas. This could lead to slower development cycles and increased technical debt.",
        "above_max_message": "Increasing Technical Skills above this much overemphasizes technical depth at the expense of collaboration and communication skills. This may create silos and hinder cross-functional teamwork."
        }},
        {{
        "entity_type": "subcategory",
        "entity_name": "Python Programming",
        "below_min_message": "...",
        "above_max_message": "..."
        }}
    ]
    }}

    Generate warnings for ALL {sum(1 + len(cat.get('subcategories', [])) for cat in persona_data.get('categories', []))} entities (categories + subcategories).
    """

    @staticmethod
    def single_entity_warning_prompt(entity_type: str, entity_data: Dict) -> str:
        """Generate warning for a single entity only (on-demand approach)"""
        
        entity_name = entity_data['name']
        weight = entity_data['weight']
        range_min = entity_data['range_min']
        range_max = entity_data['range_max']
        lower=weight - range_min
        upper=weight + range_max
        context = f"Entity Type: {entity_type}\n"
        context += f"Entity: {entity_name}\n"
        context += f"Current Weight: {weight}%\n"
        context += f"Range: {range_min}% to {range_max}%\n"
        
        if entity_type == 'subcategory':
            context += f"Parent Category: {entity_data.get('parent_category', 'N/A')}\n"
            if entity_data.get('technologies'):
                context += f"Technologies: {', '.join(entity_data['technologies'])}\n"
        
        return f"""{context}

    Generate TWO warning messages for this specific entity:

    1. **below_min_message**: What happens if weight goes BELOW {range_min}%?
    2. **above_max_message**: What happens if weight goes ABOVE {range_max}%?

    Rules:
    - Each message: 2 sentences max
    - Be specific to this entity and its actual range values
    - Focus on practical hiring impact
    - Mention the actual {range_min}% and {range_max}% values in messages

    Return JSON (no markdown):
    {{
    "below_min_message": "Reducing {entity_name} below lower% may...",
    "above_max_message": "Increasing {entity_name} above upper% could..."
    }}
    """