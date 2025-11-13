from typing import Dict, Any
import json
import time
from .base import PersonaGeneratorService2
from .persona_analyzer2 import PersonaAnalyzer2
from .llm_weight_generator import LLMWeightGeneratorV2
from .persona_structure_builder2 import PersonaStructureBuilderV2
from .persona_llm_validator import PersonaLLMValidator

from app.services.llm.OpenAIClient import OpenAIClient
from app.services.ai_tracing.action_types import ActionType
from .persona_warning_generator2 import PersonaWarningGenerator2
class OpenAIPersonaGeneratorV2(PersonaGeneratorService2):
    """Complete persona generation using pure LLM approach for weights"""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAIClient(api_key=api_key)
        self.model = model

        # Initialize phase components
        self.analyzer = PersonaAnalyzer2(self.client, model)
        self.weight_generator = LLMWeightGeneratorV2(self.client, 'gpt-4o')
        self.structure_builder = PersonaStructureBuilderV2(self.client, "gpt-4o-mini")
        self.validator = PersonaLLMValidator(self.client, model)
        self.warning_generator = PersonaWarningGenerator2(
            self.client,
            model
        )

    def export_to_json(self, persona: Dict, filename: str = "persona_output.json"):
        """Export persona to JSON file."""
        with open(filename, 'w') as f:
            json.dump(persona, f, indent=2)
        return filename
    async def generate_persona_from_jd(self, jd_text: str, jd_id: str) -> Dict[str, Any]:
        """
        Complete 4-phase persona generation with pure LLM weights.

        Args:
            jd_text: Job description text
            jd_id: Job description ID

        Returns:
            Dict matching PersonaCreate schema
        """
        start1=time.time()
        print("🔍 Phase 1: Analyzing JD...")
        analysis = await self.analyzer.analyze_jd(jd_text)
        end1=time.time()
        print(f"Time taken for analysis: {end1-start1}")
        #print(analysis)
        start2=time.time()
        print("🤖 Phase 2: Generating weights with LLM...")
        weights_data = await self.weight_generator.generate_weights(jd_text, analysis)
        end2=time.time()
        print(f"Time taken for weights: {end2-start2}")
        # print(f'weights data after normalize: {weights_data["main_categories"]}\n')
        # print(weights_data['subcategories'])
        # print(weights_data['overall_reasoning'])
        # print(weights_data['verification'])
        # Extract main weights
        main_weights = {
            key: weights_data['main_categories'][key]['weight']
            for key in weights_data['main_categories']
        }

        print(f"📊 LLM-Generated Weights:")
        print(f"   Technical: {main_weights['technical']}%")
        print(f"   Cognitive: {main_weights['cognitive']}%")
        print(f"   Values: {main_weights['values']}%")
        print(f"   Behavioral: {main_weights['behavioral']}%")
        print(f"   Leadership: {main_weights['leadership']}%")
        print(f"   Education: {main_weights['education_experience']}%")
        print(f"   Reasoning: {weights_data.get('overall_reasoning', 'N/A')}")
        start3=time.time()
        print("📝 Phase 3: Building structured persona...")
        personab = await self.structure_builder.build_persona(
            jd_text=jd_text,
            jd_id=jd_id,
            analysis=analysis,
            weights_data=weights_data
        )
        end3=time.time()
        print(f"Time taken for persona: {end3-start3}")
        #print(persona)

        start4=time.time()
        print("✅ Phase 4: LLM Validation...")
        persona = await self.validator.validate_and_correct(
            persona=personab,
            analysis=analysis,
            jd_text=jd_text,
            original_weights=weights_data
        )
        end4=time.time()
        print(f"Time taken for validation: {end4-start4}")

        # Add analysis insights
        persona['analysis_insights'] = {
            'job_family': analysis['role_understanding']['job_family'],
            'technical_intensity': analysis['technical_requirements'].get('technical_intensity'),
            'seniority_level': analysis['role_understanding']['seniority_level'],
            'weight_logic': weights_data.get('overall_reasoning', 'LLM-generated weights'),
            'weight_reasoning': {
                cat: weights_data['main_categories'][cat]['reasoning']
                for cat in weights_data['main_categories']
            }
        }
        # personaf=dict()
        # personaf['persona']=persona
        # personaf['analysis']=analysis
        # personaf['weights_data']=weights_data
        # personaf['before validation']=personab


        return persona