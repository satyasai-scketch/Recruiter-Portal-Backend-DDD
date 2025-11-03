from typing import Dict, Any
from .base import PersonaGeneratorService
from .persona_analyzer import PersonaAnalyzer
from .persona_weight_calculator import PersonaWeightCalculator
from .persona_structure_builder import PersonaStructureBuilder
from .persona_validator import PersonaValidator
from .persona_self_validator import PersonaSelfValidator
from app.services.llm.OpenAIClient import OpenAIClient
from app.services.ai_tracing.action_types import ActionType
from .persona_warning_generator import PersonaWarningGenerator

class OpenAIPersonaGenerator(PersonaGeneratorService):
    """Complete persona generation using OpenAI"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.model = model
        
        # Initialize phase components with specific action types
        # Each component gets its own client with the appropriate action type
        self.analyzer = PersonaAnalyzer(
            OpenAIClient(api_key=api_key, action_type=ActionType.PERSONA_ANALYZE),
            model
        )
        self.weight_calculator = PersonaWeightCalculator()
        self.structure_builder = PersonaStructureBuilder(
            OpenAIClient(api_key=api_key, action_type=ActionType.PERSONA_GEN),
            model
        )
        self.validator = PersonaValidator()
        self.self_validator = PersonaSelfValidator(
            OpenAIClient(api_key=api_key, action_type=ActionType.PERSONA_VALIDATE),
            model
        )
        self.warning_generator = PersonaWarningGenerator(
            OpenAIClient(api_key=api_key, action_type=ActionType.PERSONA_WEIGHT),
            model
        )
    
    async def generate_persona_from_jd(self, jd_text: str, jd_id: str) -> Dict[str, Any]:
        """
        Complete 4-phase persona generation.
        
        Args:
            jd_text: Job description text
            jd_id: Job description ID
            
        Returns:
            Dict matching PersonaCreate schema
        """
        print("🔍 Phase 1: Analyzing JD...")
        analysis = await self.analyzer.analyze_jd(jd_text)
        #print(analysis)
        print("⚖️  Phase 2: Calculating weights...")
        main_weights = self.weight_calculator.calculate_main_weights(analysis)
        edu_split = self.weight_calculator.calculate_education_split(analysis)
        
        print(f"📊 Weights: Technical={main_weights['technical']}%, Cognitive={main_weights['cognitive']}%, Values={main_weights['values']}%, Behavioral={main_weights['behavioral']}%, Leadership={main_weights['leadership']}%, Education={main_weights['education_experience']}%")
        
        print("📝 Phase 3: Building structured persona...")
        persona = await self.structure_builder.build_persona(
            jd_text=jd_text,
            jd_id=jd_id,
            analysis=analysis,
            main_weights=main_weights,
            edu_split=edu_split
        )
        
        print("✅ Phase 4: Validating...")
        validation = self.validator.validate_persona(persona)
        
        if not validation['is_valid']:
            print(f"⚠️  Auto-correcting: {validation['errors']}")
            persona = self.validator.auto_correct_weights(persona, main_weights)
        print("🔍 Phase 5: Self-validation...")
        persona = await self.self_validator.validate_and_correct(
            persona=persona,
            analysis=analysis,
            jd_text=jd_text,
            weight_calculator=self.weight_calculator
        )
        # Add analysis insights
        persona['analysis_insights'] = {
            'job_family': analysis['role_understanding']['job_family'],
            'technical_intensity': analysis['technical_requirements'].get('technical_intensity'),
            'seniority_level': analysis['role_understanding']['seniority_level'],
            'weight_logic': f"Technical {main_weights['technical']}% (intensity: {analysis['technical_requirements'].get('technical_intensity')}), Leadership {main_weights['leadership']}% (has component: {analysis['leadership_requirements'].get('has_leadership_component')})"
        }
        
        return persona