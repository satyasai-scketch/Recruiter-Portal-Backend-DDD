from typing import Dict, Any
from app.services.cv_scoring.base import CVScoringServiceBase
from app.services.cv_scoring.semantic_matcher import SemanticMatcher
from app.services.cv_scoring.lightweight_screener import LightweightScreener
from app.services.cv_scoring.detailed_scorer import DetailedScorer
from app.services.embedding.openai_service import OpenAIEmbeddingService
from app.core.config import settings
from app.services.llm.OpenAIClient import OpenAIClient
from app.services.ai_tracing.action_types import ActionType


class CVScoringService(CVScoringServiceBase):
    """
    Internal 3-stage CV scoring pipeline.
    Used by main CVScoringService in app/services/
    """
    
    def __init__(self, api_key: str):
        # Initialize embedding service with config model
        embedding_service = OpenAIEmbeddingService(
            api_key=api_key,
            model=getattr(settings, "CV_SCORING_EMBEDDING_MODEL", "text-embedding-3-small")
        )
        
        # Initialize all stage components with config models and specific action types
        self.stage1 = SemanticMatcher(embedding_service)
        self.stage2 = LightweightScreener(
            OpenAIClient(api_key=api_key, action_type=ActionType.CV_SCREEN),
            model=getattr(settings, "CV_SCORING_SCREENING_MODEL", "gpt-4o-mini")
        )
        self.stage3 = DetailedScorer(
            OpenAIClient(api_key=api_key, action_type=ActionType.CV_SCORE),
            model=getattr(settings, "CV_SCORING_DETAILED_MODEL", "gpt-4o")
        )
    
    async def score_cv(self, cv_text: str, persona: Dict) -> Dict[str, Any]:
        """
        Complete 3-stage scoring pipeline.
        
        Args:
            cv_text: Raw CV text (string)
            persona: Persona dict
            
        Returns:
            Dict with scoring results
        """
        print("=" * 80)
        print("🎯 CV SCORING PIPELINE")
        print("=" * 80)
        
        # ========== STAGE 1: EMBEDDING PRE-FILTER ==========
        stage1_result = await self.stage1.calculate_semantic_match(cv_text, persona)
        print(f"\n✓ Stage 1: {stage1_result['score']}% - {stage1_result['decision']}")
        
        if stage1_result['decision'] == 'REJECT':
            print(f"\n❌ REJECTED: {stage1_result['reason']}")
            return {
                'pipeline_stage_reached': 1,
                'stage1': stage1_result,
                'stage2': None,
                'stage3': None,
                'final_decision': 'REJECTED',
                'final_score': stage1_result['score'],
                'rejection_stage': 'embedding_prefilter',
                'rejection_reason': stage1_result['reason']
            }
        
        # ========== STAGE 2: LIGHTWEIGHT SCREENING ==========
        stage2_result = await self.stage2.screen_cv(
            cv_text=cv_text,
            persona=persona,
            embedding_score=stage1_result['score']
        )
        print(f"✓ Stage 2: {stage2_result['relevance_score']}% - {stage2_result['decision']}")
        print(f"  Skills found: {len(stage2_result.get('skills', []))}")
        
        roles = stage2_result.get('roles_detected', [])
        if roles:
            print(f"  Roles detected: {', '.join(roles[:3])}")
            if len(roles) > 3:
                print(f"  ...and {len(roles) - 3} more")
        
        if stage2_result['decision'] == 'REJECT':
            print(f"\n❌ REJECTED: {stage2_result['reason']}")
            return {
                'pipeline_stage_reached': 2,
                'stage1': stage1_result,
                'stage2': stage2_result,
                'stage3': None,
                'final_decision': 'REJECTED',
                'final_score': stage2_result['relevance_score'],
                'rejection_stage': 'lightweight_screening',
                'rejection_reason': stage2_result['reason']
            }
        
        # ========== STAGE 3: DETAILED SCORING ==========
        stage3_result = await self.stage3.score_cv_detailed(
            cv_text=cv_text,
            persona=persona,
            stage1_score=stage1_result['score'],
            stage2_score=stage2_result['relevance_score']
        )
        print(f"✓ Stage 3: {stage3_result['overall_score']:.2f}% - {stage3_result['recommendation']}")
        print(f"\n✅ COMPLETE")
        print("=" * 80)
        
        return {
            'pipeline_stage_reached': 3,
            'stage1': stage1_result,
            'stage2': stage2_result,
            'stage3': stage3_result,
            'final_decision': stage3_result['recommendation'],
            'final_score': stage3_result['overall_score'],
            'score_progression': {
                'embedding': stage1_result['score'],
                'lightweight_llm': stage2_result['relevance_score'],
                'detailed_llm': stage3_result['overall_score']
            }
        }
    
    def format_results(self, result: Dict) -> str:
        """Format detailed results for display"""
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("📊 CV SCORING RESULTS")
        lines.append("=" * 80)
        
        lines.append(f"\nFinal Decision: {result['final_decision']}")
        lines.append(f"Final Score: {result.get('final_score', 0):.2f}%")
        lines.append(f"Pipeline Reached: Stage {result['pipeline_stage_reached']}/3")
        
        # Stage 2 info
        if result.get('stage2'):
            stage2 = result['stage2']
            lines.append(f"\n{'='*80}")
            lines.append("STAGE 2: QUICK ASSESSMENT")
            lines.append(f"{'='*80}")
            lines.append(f"\nRelevance Score: {stage2.get('relevance_score', 0):.1f}%")
            lines.append(f"Assessment: {stage2.get('quick_assessment', 'N/A')}")
            
            if stage2.get('skills'):
                lines.append(f"\nSkills Detected ({len(stage2['skills'])}):")
                lines.append(f"  {', '.join(stage2['skills'][:20])}")
                if len(stage2['skills']) > 20:
                    lines.append(f"  ...and {len(stage2['skills']) - 20} more")
            
            if stage2.get('roles_detected'):
                lines.append(f"\nSuitable Roles:")
                for role in stage2['roles_detected']:
                    lines.append(f"  • {role}")
        
        # Stage 3 detailed breakdown
        if result['pipeline_stage_reached'] >= 3 and result['stage3']:
            stage3 = result['stage3']
            
            lines.append(f"\n{'='*80}")
            lines.append("STAGE 3: DETAILED CATEGORY BREAKDOWN")
            lines.append(f"{'='*80}")
            
            for cat in stage3.get('categories', []):
                lines.append(f"\n📁 {cat['name']} (Weight: {cat['weight']}%)")
                lines.append(f"   Category Score: {cat.get('category_score_percentage', 0):.2f}%")
                lines.append(f"   Contribution: {cat.get('category_contribution', 0):.2f}%")
                lines.append(f"   {'-'*76}")
                
                for sub in cat.get('subcategories', []):
                    score = sub.get('scored_percentage', 0)
                    match_symbol = "✓" if score >= 75 else "⚠" if score >= 50 else "✗"
                    
                    lines.append(f"   {match_symbol} {sub['name']}")
                    lines.append(f"      Weight: {sub['weight']}% | Level: {sub['actual_level']}/{sub['expected_level']} | Score: {score:.1f}%")
                    
                    if sub.get('missing_count', 0) > 0:
                        lines.append(f"      Missing: {sub['missing_count']} required items")
                    
                    if sub.get('notes'):
                        notes = sub['notes'][:200] + "..." if len(sub['notes']) > 200 else sub['notes']
                        lines.append(f"      Notes: {notes}")
            
            lines.append(f"\n{'='*80}")
            lines.append("FINAL ASSESSMENT")
            lines.append(f"{'='*80}")
            lines.append(f"\nRecommendation: {stage3.get('recommendation', 'N/A')}")
            lines.append(f"Reasoning: {stage3.get('reasoning', 'N/A')}")
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)