import asyncio
from typing import Dict, List, Any
import json
from app.services.cv_scoring.scoring_prompts import CVScoringPrompts
from app.services.llm.OpenAIClient import OpenAIClient


class DetailedScorer:
    """Stage 3: Deep scoring with parallel processing and stricter penalties"""

    def __init__(self, client: OpenAIClient, model: str = "gpt-4o"):
        self.client = client
        self.model = model

    async def score_cv_detailed(
        self,
        cv_text: str,
        persona: Dict,
        stage1_score: float,
        stage2_score: float
    ) -> Dict[str, Any]:
        """Deep scoring with parallel category evaluation for speed"""
        print("🤖 Stage 3: Detailed LLM scoring (parallel processing)...")

        try:
            # Score all categories in parallel
            categories = persona.get('categories', [])

            tasks = [
                self._score_category(
                    cv_text=cv_text,
                    category=cat,
                    stage1_score=stage1_score,
                    stage2_score=stage2_score
                )
                for cat in categories
            ]

            category_results = await asyncio.gather(*tasks)

            # Calculate overall score
            overall_score = sum(
                cat['category_contribution']
                for cat in category_results
            )

            # Generate final summary
            summary = await self._generate_summary(
                cv_text=cv_text,
                category_results=category_results,
                overall_score=overall_score,
                persona=persona
            )

            return {
                'overall_score': round(overall_score, 2),
                'categories': category_results,
                **summary
            }

        except Exception as e:
            raise ValueError(f"Error in detailed scoring: {str(e)}")

    async def _score_category(
        self,
        cv_text: str,
        category: Dict,
        stage1_score: float,
        stage2_score: float
    ) -> Dict[str, Any]:
        """Score a single category with all its subcategories"""

        prompt = CVScoringPrompts.category_scoring_prompt(
            cv_text=cv_text,
            category=category,
            stage1_score=stage1_score,
            stage2_score=stage2_score
        )

        messages = [
            {
                "role": "system",
                "content": "You are an expert CV evaluator. Provide evidence-based, granular scoring with strict penalties for missing requirements."
            },
            {"role": "user", "content": prompt}
        ]

        response = await self.client.chat_completion(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Add category metadata
        result['name'] = category['name']
        result['weight'] = category['weight_percentage']

        # Calculate category contribution to overall score
        subcats = result.get('subcategories', [])
        if subcats:
            # Weighted average of subcategory scores
            total_weight = sum(sub['weight'] for sub in subcats)
            weighted_sum = sum(
                sub['scored_percentage'] * sub['weight']
                for sub in subcats
            )
            category_score = weighted_sum / total_weight if total_weight > 0 else 0

            # Calculate contribution to overall score
            category_contribution = (category['weight_percentage'] / 100) * category_score
        else:
            category_score = 0
            category_contribution = 0

        result['category_score_percentage'] = round(category_score, 2)
        result['category_contribution'] = round(category_contribution, 2)

        return result

    async def _generate_summary(
        self,
        cv_text: str,
        category_results: List[Dict],
        overall_score: float,
        persona: Dict
    ) -> Dict[str, Any]:
        """Generate final summary with strengths, gaps, and recommendation"""

        # Build compact category summary for context
        cat_summary = []
        for cat in category_results:
            avg_score = cat['category_score_percentage']
            cat_summary.append(
                f"{cat['name']}: {avg_score:.1f}% "
                f"(contributes {cat['category_contribution']:.1f}% to overall)"
            )

        prompt = CVScoringPrompts.summary_prompt(
            cv_text=cv_text,
            category_summary=cat_summary,
            overall_score=overall_score,
            persona_name=persona.get('name', 'Position')
        )

        messages = [
            {
                "role": "system",
                "content": "You are an expert recruiter. Provide honest assessment based on scoring data."
            },
            {"role": "user", "content": prompt}
        ]

        response = await self.client.chat_completion(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)