from typing import Dict, Any
import json

class PersonaPrompts:
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
    def persona_structure_prompt(
        jd_text: str,
        analysis: Dict,
        main_weights: Dict[str, int],
        edu_split: Dict[str, int],
        jd_id: str
    ) -> str:
        """Phase 3: Structured persona generation prompt"""
        
        tech_req = analysis.get('technical_requirements', {})
        cog_req = analysis.get('cognitive_requirements', {})
        val_req = analysis.get('values_requirements', {})
        beh_req = analysis.get('behavioral_requirements', {})
        lead_req = analysis.get('leadership_requirements', {})
        edu_req = analysis.get('education_requirements', {})
        
        # Calculate ranges
        tech_range = PersonaPrompts._calculate_range(main_weights['technical'])
        cog_range = PersonaPrompts._calculate_range(main_weights['cognitive'])
        val_range = PersonaPrompts._calculate_range(main_weights['values'])
        beh_range = PersonaPrompts._calculate_range(main_weights['behavioral'])
        lead_range = PersonaPrompts._calculate_range(main_weights['leadership'])
        edu_range = PersonaPrompts._calculate_range(main_weights['education_experience'])
        
        import json
        
        return f"""Create a structured candidate persona based on this analysis and calculated weights.

    JOB DESCRIPTION:
    {jd_text}

    CALCULATED MAIN WEIGHTS (USE THESE EXACTLY):
    - Technical Skills: {main_weights['technical']}% (range: {tech_range[0]} to +{tech_range[1]})
    - Cognitive Demands: {main_weights['cognitive']}% (range: {cog_range[0]} to +{cog_range[1]})
    - Values (Schwartz): {main_weights['values']}% (range: {val_range[0]} to +{val_range[1]})
    - Foundational Behaviors: {main_weights['behavioral']}% (range: {beh_range[0]} to +{beh_range[1]})
    - Leadership Skills: {main_weights['leadership']}% (range: {lead_range[0]} to +{lead_range[1]})
    - Education and Experience: {main_weights['education_experience']}% (range: {edu_range[0]} to +{edu_range[1]})

    EDUCATION/EXPERIENCE SPLIT (USE EXACTLY):
    - Academic Qualification: {edu_split['education']}%
    - Years of Experience: {edu_split['experience']}%
    - Certifications & Portfolio: {edu_split['certifications']}%

    INTELLIGENCE FROM ANALYSIS:
    Technical Clusters Identified: {json.dumps(tech_req.get('skill_clusters', []), indent=2)}
    Cognitive Distribution: {json.dumps(cog_req.get('cognitive_distribution', {}), indent=2)}
    Values Focus: {json.dumps(val_req, indent=2)}
    Behavioral Emphasis: {json.dumps(beh_req, indent=2)}
    Leadership Needs: {json.dumps(lead_req, indent=2)}
    Education Requirements: {json.dumps(edu_req, indent=2)}

    CREATE PERSONA JSON:

    {{
    "job_description_id": "{jd_id}",
    "name": "{analysis['role_understanding']['title']} Persona",
    "categories": [
        {{
        "name": "Technical Skills",
        "weight_percentage": {main_weights['technical']},
        "range_min": {tech_range[0]},
        "range_max": {tech_range[1]},
        "position": 1,
        "subcategories": [
            // Create 4-6 subcategories from skill_clusters analysis above
            // Use cluster_name, skills list, and emphasis to determine weights
            // Subcategory weights MUST sum to 100
            {{
            "name": "<cluster_name from analysis>",
            "weight_percentage": <calculate based on emphasis: critical=30-40, important=20-30, nice_to_have=10-15>,
            "range_min": <-min(5, weight//7)>,
            "range_max": <min(10, weight//3.5)>,
            "level_id": "<1-5 based on technical_depth_required>",
            "position": 1,
            "skillset": {{
                "technologies": ["<actual skill names from cluster>"]
            }}
            }}
            // Repeat for each cluster, ensure total = 100
        ],
        "notes": {{"custom_notes": ""}}
        }},
        
        {{
        "name": "Cognitive Demands",
        "weight_percentage": {main_weights['cognitive']},
        "range_min": {cog_range[0]},
        "range_max": {cog_range[1]},
        "position": 2,
        "subcategories": [
            {{
            "name": "Problem Solving",
            "weight_percentage": <sum of analyze + evaluate from cognitive_distribution>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on primary_cognitive_level>",
            "position": 1,
            "skillset": {{
                "technologies": ["<Extract specific problem-solving requirements from JD>"]
            }}
            }},
            {{
            "name": "Design Thinking",
            "weight_percentage": <use create value from cognitive_distribution>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on primary_cognitive_level>",
            "position": 2,
            "skillset": {{
                "technologies": ["<Extract innovation/design requirements from JD>"]
            }}
            }},
            {{
            "name": "Attention to Detail",
            "weight_percentage": <sum of understand + apply from cognitive_distribution>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on primary_cognitive_level>",
            "position": 3,
            "skillset": {{
                "technologies": ["<Extract detail-orientation requirements from JD>"]
            }}
            }}
        ],
        "notes": {{"custom_notes": ""}}
        }},
        
        {{
        "name": "Values (Schwartz)",
        "weight_percentage": {main_weights['values']},
        "range_min": {val_range[0]},
        "range_max": {val_range[1]},
        "position": 3,
        "subcategories": [
            {{
            "name": "Creativity & Self-Direction",
            "weight_percentage": <use innovation_focus from values analysis>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on how strongly JD emphasizes this value>",
            "position": 1,
            "skillset": {{
                "technologies": ["<Extract creativity/autonomy expectations from JD>"]
            }}
            }},
            {{
            "name": "Achievement",
            "weight_percentage": <use achievement_focus from values analysis>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on how strongly JD emphasizes this value>",
            "position": 2,
            "skillset": {{
                "technologies": ["<Extract results/goal orientation from JD>"]
            }}
            }},
            {{
            "name": "Benevolence",
            "weight_percentage": <use collaboration_focus from values analysis>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on how strongly JD emphasizes this value>",
            "position": 3,
            "skillset": {{
                "technologies": ["<Extract teamwork/collaboration expectations from JD>"]
            }}
            }},
            {{
            "name": "Conformity",
            "weight_percentage": <use security_focus from values analysis>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on how strongly JD emphasizes this value>",
            "position": 4,
            "skillset": {{
                "technologies": ["<Extract compliance/process adherence from JD>"]
            }}
            }}
        ],
        "notes": {{"custom_notes": ""}}
        }},
        
        {{
        "name": "Foundational Behaviors",
        "weight_percentage": {main_weights['behavioral']},
        "range_min": {beh_range[0]},
        "range_max": {beh_range[1]},
        "position": 4,
        "subcategories": [
            {{
            "name": "Collaboration",
            "weight_percentage": <use communication_emphasis from behavioral analysis>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": ""<1-5 based on behavioral_emphasis score from analysis>",
            "position": 1,
            "skillset": {{
                "technologies": ["<Extract specific collaboration/communication needs from JD>"]
            }}
            }},
            {{
            "name": "Adaptability",
            "weight_percentage": <use resilience_emphasis from behavioral analysis>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": ""<1-5 based on behavioral_emphasis score from analysis>",
            "position": 2,
            "skillset": {{
                "technologies": ["<Extract change management/stress handling needs from JD>"]
            }}
            }},
            {{
            "name": "Ownership",
            "weight_percentage": <use decision_making_emphasis from behavioral analysis>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": ""<1-5 based on behavioral_emphasis score from analysis>",
            "position": 3,
            "skillset": {{
                "technologies": ["<Extract accountability/autonomy expectations from JD>"]
            }}
            }}
        ],
        "notes": {{"custom_notes": ""}}
        }},
        
        {{
        "name": "Leadership Skills",
        "weight_percentage": {main_weights['leadership']},
        "range_min": {lead_range[0]},
        "range_max": {lead_range[1]},
        "position": 5,
        "subcategories": [
            {{
            "name": "Mentoring & Peer Review",
            "weight_percentage": <use mentoring_emphasis from leadership analysis>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on seniority: junior=1, mid=2, senior=3, lead=4, director+=5>",
            "position": 1,
            "skillset": {{
                "technologies": ["<Extract mentoring/coaching requirements from JD>"]
            }}
            }},
            {{
            "name": "Decision Making",
            "weight_percentage": <use influence_emphasis from leadership analysis>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on seniority: junior=1, mid=2, senior=3, lead=4, director+=5>",
            "position": 2,
            "skillset": {{
                "technologies": ["<Extract stakeholder management/influence needs from JD>"]
            }}
            }},
            {{
            "name": "Strategic Vision",
            "weight_percentage": <use vision_emphasis from leadership analysis>,
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on seniority: junior=1, mid=2, senior=3, lead=4, director+=5>",
            "position": 3,
            "skillset": {{
                "technologies": ["<Extract strategic planning/long-term vision from JD>"]
            }}
            }}
        ],
        "notes": {{"custom_notes": ""}}
        }},
        
        {{
        "name": "Education and Experience",
        "weight_percentage": {main_weights['education_experience']},
        "range_min": {edu_range[0]},
        "range_max": {edu_range[1]},
        "position": 6,
        "subcategories": [
            {{
            "name": "Academic Qualification",
            "weight_percentage": {edu_split['education']},
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on education_importance>",
            "position": 1,
            "skillset": {{
                "technologies": ["<Extract exact degree requirements from JD, e.g., 'Bachelor's in CS required', 'MBA preferred'>"]
            }}
            }},
            {{
            "name": "Years of Experience",
            "weight_percentage": {edu_split['experience']},
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on years_experience_required>",
            "position": 2,
            "skillset": {{
                "technologies": ["<Extract exact experience requirements from JD, e.g., '5-7 years in software development', '3+ years leading teams'>"]
            }}
            }},
            {{
            "name": "Certifications & Portfolio",
            "weight_percentage": {edu_split['certifications']},
            "range_min": <calculate>,
            "range_max": <calculate>,
            "level_id": "<1-5 based on number of certs required>",
            "position": 3,
            "skillset": {{
                "technologies": ["<Extract certifications from JD, e.g., 'AWS Certified preferred', 'GitHub portfolio required'>"]
            }}
            }}
        ],
        "notes": {{"custom_notes": ""}}
        }}
    ]
    }}

    CRITICAL RULES:
    1. Use EXACT main category weights provided above - no changes allowed
    2. Use EXACT education split percentages provided above
    3. Each category's subcategories MUST sum to exactly 100
    4. Calculate range_min and range_max for each subcategory using formula
    5. level_id MUST be string "1" to "5"
    6. For Technical Skills: "technologies" contains actual skill/tool names
    7. For ALL other categories: "technologies" contains descriptive requirement strings
    8. Use the analysis data to inform weights - don't split evenly
    9. If analysis shows 0 emphasis, assign minimal weight (5-10%) but include the subcategory
    10. Extract specific requirements from JD text for skillset technologies

    SKILLSET "technologies" ARRAY EXAMPLES:

    Technical Skills:
    "technologies": ["Python", "React", "AWS", "PostgreSQL"]

    Cognitive - Problem Solving:
    "technologies": ["Debug complex distributed systems", "Root cause analysis", "Performance optimization"]

    Values - Achievement:
    "technologies": ["Drive measurable results and KPIs", "Exceed quarterly targets", "Data-driven decision making"]

    Behaviors - Collaboration:
    "technologies": ["Cross-functional teamwork with product and design", "Lead technical discussions", "Facilitate alignment meetings"]

    Leadership - Strategic Vision:
    "technologies": ["Long-term technical roadmap planning", "Align initiatives with business goals", "Define architecture strategy"]

    Education - Academic Qualification:
    "technologies": ["Bachelor's degree in Computer Science required", "MBA or relevant master's degree preferred"]

    Education - Years of Experience:
    "technologies": ["5-7 years in software development", "3+ years in leadership role", "Experience in fintech industry"]

    Education - Certifications:
    "technologies": ["AWS Certified Solutions Architect preferred", "PMP certification is a plus", "Strong GitHub portfolio"]

    Return ONLY valid JSON, no markdown.
    """
    @staticmethod
    def self_validation_prompt(
        persona: Dict,
        analysis: Dict,
        jd_text: str
    ) -> str:
        """Phase 5: Self-validation prompt"""
        
        tech_cat = next((c for c in persona['categories'] if c['name'] == 'Technical Skills'), None)
        cog_cat = next((c for c in persona['categories'] if c['name'] == 'Cognitive Demands'), None)
        
        tech_weight = tech_cat['weight_percentage'] if tech_cat else 0
        cog_weight = cog_cat['weight_percentage'] if cog_cat else 0
        
        tech_intensity = analysis['technical_requirements'].get('technical_intensity', 'medium')
        primary_cognitive = analysis['cognitive_requirements'].get('primary_cognitive_level', 'apply')
        
        category_weights = {c['name']: c['weight_percentage'] for c in persona['categories']}
        
        return f"""You generated a persona with these main category weights:
    - Technical Skills: {tech_weight}%
    - Cognitive Demands: {cog_weight}%
    - Values (Schwartz): {category_weights.get('Values (Schwartz)', 0)}%
    - Foundational Behaviors: {category_weights.get('Foundational Behaviors', 0)}%
    - Leadership Skills: {category_weights.get('Leadership Skills', 0)}%
    - Education and Experience: {category_weights.get('Education and Experience', 0)}%

    Original JD Analysis showed:
    - Technical Intensity: {tech_intensity}
    - Primary Cognitive Level: {primary_cognitive}
    - Job Family: {analysis['role_understanding']['job_family']}
    - Seniority: {analysis['role_understanding']['seniority_level']}

    Quick validation questions:
    1. Does {tech_weight}% technical match "{tech_intensity}" intensity?
    2. Does {cog_weight}% cognitive match "{primary_cognitive}" primary level?
    3. Are the weights reasonable for this role?

    Return JSON:
    {{
    "is_valid": true/false,
    "issues": ["list any misalignments"],
    "recommendations": {{
        "Technical Skills": {tech_weight} or <corrected value>,
        "Cognitive Demands": {cog_weight} or <corrected value>,
        "Leadership Skills": {category_weights.get('Leadership Skills', 0)} or <corrected value>
    }},
    "reasoning": "brief explanation"
    }}

    Only suggest changes if there's clear misalignment (e.g., technical=20% but intensity='very_high')."""
    
    @staticmethod
    def _calculate_range(weight: int) -> tuple:
        """Helper to calculate ranges"""
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