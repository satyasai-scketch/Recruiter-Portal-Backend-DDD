from typing import Dict, List


class CVScoringPrompts:
    """Centralized prompts for CV scoring"""
    
    @staticmethod
    def lightweight_screening_prompt(cv_text: str, persona: Dict, embedding_score: float) -> str:
        """Stage 2: Quick screening with skill extraction and role detection"""
        
        # Build compact requirements summary
        req_summary = []
        for cat in persona.get('categories', []):
            cat_line = f"{cat['name']} ({cat['weight_percentage']}%): "
            subcats = []
            for sub in cat.get('subcategories', []):
                tech_info = sub.get('skillset', {}).get('technologies', [])
                tech_count = len(tech_info)
                if tech_count > 0:
                    subcats.append(f"{sub['name']} (L{sub.get('level_id')}, {tech_count} items)")
                else:
                    subcats.append(f"{sub['name']} (L{sub.get('level_id')})")
            cat_line += ', '.join(subcats)
            req_summary.append(cat_line)

        return f"""Quick CV relevance assessment with skill extraction and role detection.

REQUIREMENTS (by importance):
{chr(10).join(req_summary)}

CV:
{cv_text[:2500]}

TASK:
1. Assess relevance to the requirements above (0-100 score)
2. Extract ALL skills mentioned in CV (technical, soft, domain-specific)
3. Detect suitable roles this candidate would fit (based on their overall profile)

Return JSON:
{{
  "relevance_score": <0-100, granular score like 73 or 86>,
  "assessment": "2-3 sentence quick assessment",
  "skills": [
    "Python", "Django", "AWS", "Docker", "Leadership", "Agile",
    "Problem Solving", "PostgreSQL", "REST APIs", "Communication"
    // List ALL skills found - technical, soft, tools, methodologies, etc.
  ],
  "roles_detected": [
    "Senior Backend Developer",
    "Python Engineer",
    "Full Stack Developer",
    "DevOps Engineer"
    // List 3-7 job roles this CV would be suitable for
  ],
  "key_matches": ["3-5 strengths matching requirements"],
  "key_gaps": ["3-5 gaps vs requirements"]
}}

IMPORTANT:
- "skills": Extract comprehensive list (not just matching requirements - ALL skills in CV)
- "roles_detected": Think broadly - what roles would this person be good for? (not just the current persona)
- Use granular scores (not just 70, 75, 80 - use 73, 78, 82, etc.)

Scoring guidance: 90-100=Excellent, 80-89=Strong, 70-79=Good, 60-69=Borderline, <60=Poor"""
    
    @staticmethod
    def category_scoring_prompt(
        cv_text: str,
        category: Dict,
        stage1_score: float,
        stage2_score: float
    ) -> str:
        """Stage 3: Category-specific detailed scoring prompt"""
        
        # Build subcategory details
        subcategories_detail = []
        for sub in category.get('subcategories', []):
            sub_block = f"\n{sub['position']}. {sub['name']}"
            sub_block += f"\n   Weight: {sub['weight_percentage']}%"
            sub_block += f"\n   Expected Level: {sub.get('level_id', 3)}"

            # Required items from skillset.technologies
            if 'skillset' in sub and 'technologies' in sub['skillset']:
                techs = sub['skillset']['technologies']
                sub_block += f"\n   Required Items ({len(techs)} total):"
                for tech in techs[:15]:  # Show first 15
                    sub_block += f"\n      - {tech}"
                if len(techs) > 15:
                    sub_block += f"\n      ... and {len(techs) - 15} more"

            subcategories_detail.append(sub_block)

        subcats_text = '\n'.join(subcategories_detail)

        return f"""Score this CV for the "{category['name']}" category only.

BASELINE SCORES:
- Quick Screen: {stage2_score:.1f}%

CATEGORY: {category['name']} (Weight: {category['weight_percentage']}% of overall score)

SUBCATEGORIES TO EVALUATE:
{subcats_text}

CV TEXT:
{cv_text}

YOUR TASK: HOLISTIC ASSESSMENT

You are an expert evaluator. Assess this subcategory by considering ALL factors together:

1. DEPTH & BREADTH:
   - How deep is their expertise? (beginner mention vs. production experience vs. expert/architect)
   - How broad is their coverage? (1 tool vs. multiple tools in this area)
   - Quality of evidence: specific projects, metrics, outcomes vs. just listing keywords

2. REQUIRED ITEMS COVERAGE:
   - Count items found vs. total required (using semantic matching)
   - But consider: Is it better to have deep expertise in 70% of items, or shallow mentions of 90%?
   - Missing critical items hurts more than missing nice-to-have items

3. RECENCY & RELEVANCE:
   - Recent experience (last 2-3 years) is most valuable
   - Experience from 3-5 years ago: still good but slightly less relevant
   - Experience >5 years old without recent updates: significantly less valuable

4. LEVEL CALIBRATION (use as reference, not rigid rules):
   - Level 5: Expert/Architect - Deep mastery, leadership, multiple advanced projects
   - Level 4: Advanced - Production experience, complex implementations, mentoring others
   - Level 3: Intermediate - Solid working knowledge, completed real projects independently
   - Level 2: Basic - Some exposure, assisted on projects, limited independent work
   - Level 1: Awareness - Knows it exists, minimal or no hands-on experience

5. SCORING GUIDANCE (not formulas - use judgment):

   EXCEEDS expectations (actual > expected):
   → 95-100% range
   - Strong depth + high coverage + recent → 98-100%
   - Strong depth + good coverage → 95-97%
   - Good depth but lower coverage → 92-95%

   MEETS expectations (actual = expected):
   → 85-95% range
   - Excellent evidence + high coverage → 92-95%
   - Strong evidence + good coverage → 88-92%
   - Solid evidence + decent coverage → 85-88%
   - Meets level but thin coverage → 82-85%

   ONE LEVEL BELOW (actual = expected - 1):
   → 60-80% range
   - Almost there, strong partial match → 75-80%
   - Good foundation but gaps → 68-75%
   - Some relevant experience but limited → 60-68%

   TWO+ LEVELS BELOW:
   → 0-55% range
   - Two levels below + some coverage → 40-55%
   - Three levels below or minimal evidence → 10-30%
   - No relevant evidence → 0-5%

IMPORTANT: Don't mechanically apply formulas. Think like a hiring manager:
- Would you confidently say this person can handle this aspect of the job?
- Are they missing critical skills or just nice-to-haves?
- Is their experience deep and recent, or shallow and dated?
- Does the overall picture inspire confidence?

Use GRANULAR scores (67%, 83%, 91%) that reflect your honest assessment.

CRITICAL RULES:
1. Use SEMANTIC matching (abbreviations, related fields) - NOT keyword matching
2. Extract actual CV quotes as evidence in your notes
3. Think holistically: depth + breadth + coverage + recency all together
4. Be fair but honest: Don't inflate scores, but recognize transferable skills
5. Consider: Would a hiring manager be confident this person can do the job?

Return JSON:
{{
  "subcategories": [
    {{
      "name": "<subcategory name>",
      "weight": <weight_percentage>,
      "expected_level": <from persona>,
      "actual_level": <1-5 from CV>,
      "base_score": <score before applying coverage adjustment>,
      "coverage_ratio": <0.0-1.0, decimal like 0.75 or 0.90>,
      "missing_count": <number of missing required items>,
      "scored_percentage": <final 0-100 after penalties>,
      "notes": "<Explain: level assessment, what was found vs missing, evidence quotes, why this score>"
    }}
  ]
}}

Evaluate ALL subcategories listed above."""
    
    @staticmethod
    def summary_prompt(
        cv_text: str,
        category_summary: List[str],
        overall_score: float,
        persona_name: str
    ) -> str:
        """Stage 3: Final summary generation prompt"""
        
        return f"""Generate final assessment summary.

OVERALL SCORE: {overall_score:.2f}%

CATEGORY BREAKDOWN:
{chr(10).join(category_summary)}

CV:
{cv_text}

PERSONA REQUIREMENTS:
Role: {persona_name}

Return JSON:
{{
  "strengths": ["3-5 key strengths with evidence"],
  "gaps": ["3-5 critical gaps vs requirements"],
  "recommendation": "<STRONG_MATCH | GOOD_FIT | MODERATE_FIT | WEAK_FIT>",
  "reasoning": "<2-3 sentences explaining overall_score and recommendation>"
}}

Recommendation Guidelines:
- STRONG_FIT: 80-100%, minimal gaps, exceeds key requirements
- GOOD_FIT: 70-80%, some gaps but solid match on critical areas
- MODERATE_FIT: 60-69%, significant gaps but has potential
- WEAK_FIT: <60%, major gaps in critical areas"""