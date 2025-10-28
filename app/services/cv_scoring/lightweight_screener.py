from typing import Dict, Any
from openai import AsyncOpenAI
import json
from app.services.cv_scoring.scoring_prompts import CVScoringPrompts


class LightweightScreener:
    """Stage 2: Quick LLM screening with skill extraction and role detection"""

    def __init__(self, client: AsyncOpenAI, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model
        self.min_threshold = 70.0
        self.strong_match_threshold = 80.0

    async def screen_cv(
        self,
        cv_text: str,
        persona: Dict,
        embedding_score: float
    ) -> Dict[str, Any]:
        """Quick relevance check with skill and role detection"""
        print("🔍 Stage 2: Lightweight LLM screening...")

        try:
            prompt = CVScoringPrompts.lightweight_screening_prompt(
                cv_text=cv_text,
                persona=persona,
                embedding_score=embedding_score
            )

            messages = [
                {
                    "role": "system",
                    "content": "You are a quick CV screener. Assess CV relevance, extract skills, and detect suitable roles."
                },
                {"role": "user", "content": prompt}
            ]

            response = await self.client.chat_completion(
                model=self.model,
                messages=messages,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            quick_score = result.get('relevance_score', 0)

            if quick_score < self.min_threshold:
                decision = 'REJECT'
                next_stage = None
                reason = f"Quick LLM score too low ({quick_score}% < {self.min_threshold}%)"
            else:
                decision = 'PASS_TO_STAGE3'
                next_stage = 'detailed_scoring'
                if quick_score >= self.strong_match_threshold:
                    reason = f"Strong match ({quick_score}% ≥ {self.strong_match_threshold}%)"
                else:
                    reason = f"Borderline match ({quick_score}% in 70-80% range)"

            return {
                'stage': 2,
                'method': 'lightweight_llm',
                'model': self.model,
                'relevance_score': quick_score,
                'min_threshold': self.min_threshold,
                'decision': decision,
                'reason': reason,
                'next_stage': next_stage,
                'quick_assessment': result.get('assessment', ''),
                'skills': result.get('skills', []),
                'roles_detected': result.get('roles_detected', []),
                'key_matches': result.get('key_matches', []),
                'key_gaps': result.get('key_gaps', [])
            }

        except Exception as e:
            raise ValueError(f"Error in lightweight screening: {str(e)}")