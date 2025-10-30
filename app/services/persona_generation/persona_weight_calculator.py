from typing import Dict


class PersonaWeightCalculator:
    """Phase 2: Calculate intelligent weights from analysis"""
    
    @staticmethod
    def calculate_main_weights(analysis: Dict) -> Dict[str, int]:
        """Calculate category weights based on JD analysis"""
        role = analysis.get('role_understanding', {})
        tech = analysis.get('technical_requirements', {})
        cog = analysis.get('cognitive_requirements', {})
        val = analysis.get('values_requirements', {})
        beh = analysis.get('behavioral_requirements', {})
        lead = analysis.get('leadership_requirements', {})
        edu = analysis.get('education_requirements', {})
        context = analysis.get('context_signals', {})
        
        weights = {
            'technical': 20,
            'cognitive': 20,
            'values': 20,
            'behavioral': 20,
            'leadership': 10,
            'education_experience': 10
        }
        
        # Technical weight
        technical_score = 0
        num_clusters = len(tech.get('skill_clusters', []))
        technical_score += min(15, num_clusters * 3)
        
        intensity_map = {'none': 0, 'low': 5, 'medium': 15, 'high': 25, 'very_high': 35}
        technical_score += intensity_map.get(tech.get('technical_intensity', 'medium'), 15)
        
        depth_map = {'beginner': 0, 'intermediate': 5, 'advanced': 10, 'expert': 15}
        technical_score += depth_map.get(tech.get('technical_depth_required', 'intermediate'), 5)
        
        if not tech.get('has_technical_requirements', True):
            technical_score = 5
        
        weights['technical'] = min(70, 20 + technical_score)
        
        # Cognitive weight
        cognitive_score = 0
        primary_level = cog.get('primary_cognitive_level', 'apply')
        complexity_map = {'understand': 5, 'apply': 10, 'analyze': 15, 'evaluate': 20, 'create': 25}
        cognitive_score += complexity_map.get(primary_level, 10)
        
        cog_dist = cog.get('cognitive_distribution', {})
        high_level_score = int(cog_dist.get('evaluate', 0) or 0) + int(cog_dist.get('create', 0) or 0)
        cognitive_score += min(15, high_level_score / 10)
        weights['cognitive'] = min(40, 20 + cognitive_score)
        
        # Values weight
        values_score = 0
        total_values = sum([
            int(val.get('achievement_focus', 0) or 0),
            int(val.get('security_focus', 0) or 0),
            int(val.get('innovation_focus', 0) or 0),
            int(val.get('collaboration_focus', 0) or 0)
        ])
        values_score += min(20, total_values / 10)
        
        if int(val.get('security_focus', 0) or 0) > 50:
            values_score += 10
        if context.get('process_driven', False):
            values_score += 5
        
        weights['values'] = min(35, 20 + values_score)
        
        # Behavioral weight
        behavioral_score = 0
        total_behavioral = sum([
            int(beh.get('communication_emphasis', 0) or 0),
            int(beh.get('resilience_emphasis', 0) or 0),
            int(beh.get('decision_making_emphasis', 0) or 0),
            int(beh.get('detail_orientation_emphasis', 0) or 0)
        ])
        behavioral_score += min(15, total_behavioral / 10)
        
        if context.get('customer_facing', False):
            behavioral_score += 10
        if context.get('fast_paced', False):
            behavioral_score += 5
        if context.get('cross_functional_heavy', False):
            behavioral_score += 5
        
        weights['behavioral'] = min(35, 20 + behavioral_score)
        
        # Leadership weight
        leadership_score = 0
        if not lead.get('has_leadership_component', False):
            leadership_score = -10
        else:
            total_leadership = sum([
                int(lead.get('mentoring_emphasis', 0) or 0),
                int(lead.get('influence_emphasis', 0) or 0),
                int(lead.get('vision_emphasis', 0) or 0),
                int(lead.get('process_emphasis', 0) or 0)
            ])
            leadership_score += min(25, total_leadership / 8)
        
        seniority = role.get('seniority_level', 'mid')
        seniority_boost = {
            'junior': -5, 'mid': 0, 'senior': 5, 'lead': 10,
            'principal': 12, 'manager': 15, 'director': 20, 'vp': 25, 'executive': 30
        }
        leadership_score += seniority_boost.get(seniority, 0)
        weights['leadership'] = max(3, min(40, 10 + leadership_score))
        
        # Education weight
        education_score = 0
        importance_map = {'critical': 5, 'important': 2, 'preferred': 0, 'not_mentioned': -3}
        education_score += importance_map.get(edu.get('education_importance', 'preferred'), 0)
        
        if edu.get('specific_degrees_required') or edu.get('certifications_required'):
            education_score += 3
        
        years = edu.get('years_experience_required', 0)
        if years and years >= 10:
            education_score -= 3
        elif years and years >= 5:
            education_score -= 1
        elif years == 0:
            education_score += 5
        
        weights['education_experience'] = max(2, min(15, 10 + education_score))
        #print("Calculated weights before normalization:")
        #print(weights)
        return PersonaWeightCalculator._normalize_weights(weights)
    
    @staticmethod
    def calculate_education_split(analysis: Dict) -> Dict[str, int]:
        """Calculate education vs experience vs certifications split"""
        edu_req = analysis.get('education_requirements', {})
        edu_importance = edu_req.get('education_importance', 'preferred')
        years_required = edu_req.get('years_experience_required')
        can_substitute = edu_req.get('can_substitute_education', True)
        
        # Fresher/Entry-level
        if years_required == 0 or (years_required is None and 'junior' in analysis['role_understanding']['seniority_level'].lower()):
            return {'education': 50, 'experience': 30, 'certifications': 20}
        
        # Education not mentioned
        if edu_importance == 'not_mentioned' and not edu_req.get('specific_degrees_required'):
            if years_required and years_required >= 5:
                return {'education': 20, 'experience': 60, 'certifications': 20}
            return {'education': 30, 'experience': 50, 'certifications': 20}
        
        # Experience not mentioned but education critical
        if edu_importance == 'critical' and (years_required is None or years_required == 0):
            return {'education': 60, 'experience': 20, 'certifications': 20}
        
        # Standard cases
        if edu_importance == 'critical' and not can_substitute:
            if years_required and years_required >= 5:
                return {'education': 45, 'experience': 40, 'certifications': 15}
            return {'education': 50, 'experience': 30, 'certifications': 20}
        
        if edu_importance == 'critical' and can_substitute:
            return {'education': 40, 'experience': 40, 'certifications': 20}
        
        if edu_importance == 'important':
            if years_required and years_required >= 8:
                return {'education': 30, 'experience': 50, 'certifications': 20}
            return {'education': 40, 'experience': 40, 'certifications': 20}
        
        if edu_importance == 'preferred':
            if years_required and years_required >= 5:
                return {'education': 30, 'experience': 50, 'certifications': 20}
            return {'education': 35, 'experience': 45, 'certifications': 20}
        
        return {'education': 40, 'experience': 40, 'certifications': 20}
    
    @staticmethod
    def _normalize_weights(weights: Dict[str, float]) -> Dict[str, int]:
        """Ensure weights sum to exactly 100"""
        for cat in weights:
            weights[cat] = max(2, weights[cat])
        
        total = sum(weights.values())
        if total == 0:
            return {cat: int(w) for cat, w in weights.items()}
        
        factor = 100 / total
        normalized = {cat: int(round(w * factor)) for cat, w in weights.items()}
        #print("Normalized weights before adjustment:")
        #print(normalized)
        current_sum = sum(normalized.values())
        difference = 100 - current_sum
        
        if difference != 0:
            largest = max(normalized, key=normalized.get)
            normalized[largest] += difference
        
        return normalized