from typing import Dict, List
import numpy as np
from app.services.embedding.openai_service import OpenAIEmbeddingService


class SemanticMatcher:
    """Stage 1: Fast embedding-based pre-filtering (60% threshold)"""

    def __init__(self, embedding_service: OpenAIEmbeddingService):
        self.embedding_service = embedding_service
        self.threshold = 60.0

    async def calculate_semantic_match(self, cv_text: str, persona: Dict) -> Dict:
        """Calculate semantic similarity between CV and persona"""
        print("📊 Stage 1: Embedding-based pre-filtering...")

        persona_text = self._extract_persona_text(persona)

        print("   Generating embeddings...")
        cv_embedding = await self.embedding_service.embed_text(cv_text)
        persona_embedding = await self.embedding_service.embed_text(persona_text)

        similarity = self._cosine_similarity(
            np.array(cv_embedding),
            np.array(persona_embedding)
        )

        similarity_score = similarity * 100

        if similarity_score < self.threshold:
            decision = 'REJECT'
            reason = f"Semantic match too low ({similarity_score:.1f}% < {self.threshold}% threshold)"
            next_stage = None
        else:
            decision = 'PASS_TO_STAGE2'
            reason = f"Semantic match sufficient ({similarity_score:.1f}% ≥ {self.threshold}%)"
            next_stage = 'lightweight_screening'

        return {
            'stage': 1,
            'method': 'embedding_similarity',
            'score': round(similarity_score, 2),
            'threshold': self.threshold,
            'decision': decision,
            'reason': reason,
            'next_stage': next_stage
        }

    def _extract_persona_text(self, persona: Dict) -> str:
        """Extract role title and skills/technologies grouped by category"""

        # Start with role title
        role_name = persona.get('name', 'Position')
        parts = [f"Role: {role_name}"]

        # Group requirements by category for better semantic matching
        for category in persona.get('categories', []):
            cat_name = category['name']
            cat_requirements = []

            for subcat in category.get('subcategories', []):
                if 'skillset' in subcat and 'technologies' in subcat['skillset']:
                    techs = subcat['skillset']['technologies']
                    cat_requirements.extend(techs)

            # Add category block if it has requirements
            if cat_requirements:
                # Keep duplicates within category context
                parts.append(f"{cat_name}: {', '.join(cat_requirements)}")

        return '\n'.join(parts)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        return dot_product / (norm1 * norm2)