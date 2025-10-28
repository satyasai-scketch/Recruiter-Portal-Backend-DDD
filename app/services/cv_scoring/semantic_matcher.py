from typing import Dict, List
import numpy as np
from app.services.embedding.openai_service import OpenAIEmbeddingService
import re


class SemanticMatcher:
    """Stage 1: CV chunking with embedding-based best match selection"""

    def __init__(self, embedding_service: OpenAIEmbeddingService):
        self.embedding_service = embedding_service
        self.best_chunk_min = 50.0

    async def calculate_semantic_match(self, cv_text: str, persona: Dict) -> Dict:
        """Calculate match using CV chunking approach"""
        print("📊 Stage 1: CV Chunking with best match selection...")

        persona_text = self._extract_persona_requirements(persona)
        chunks = self._chunk_cv(cv_text)
        print(f"   Created {len(chunks)} CV chunks")

        persona_embedding = await self.embedding_service.embed_text(persona_text)

        chunk_scores = []
        for i, chunk in enumerate(chunks):
            chunk_embedding = await self.embedding_service.embed_text(chunk['text'])
            
            similarity = self._cosine_similarity(
                np.array(chunk_embedding),
                np.array(persona_embedding)
            )
            similarity_score = similarity * 100
            
            chunk_scores.append({
                'chunk_index': i,
                'chunk_type': chunk['type'],
                'similarity_score': similarity_score,
                'preview': chunk['text'][:150] + "..."
            })

        best_chunk = max(chunk_scores, key=lambda x: x['similarity_score'])
        
        print(f"   Best chunk: #{best_chunk['chunk_index']} ({best_chunk['chunk_type']}) - {best_chunk['similarity_score']:.1f}%")

        if best_chunk['similarity_score'] < self.best_chunk_min:
            decision = 'REJECT'
            reason = f"Best chunk score too low ({best_chunk['similarity_score']:.1f}% < {self.best_chunk_min}%)"
            next_stage = None
        else:
            decision = 'PASS_TO_STAGE2'
            reason = f"Best chunk passes threshold (similarity: {best_chunk['similarity_score']:.1f}%)"
            next_stage = 'lightweight_screening'

        return {
            'stage': 1,
            'method': 'cv_chunking',
            'score': round(best_chunk['similarity_score'], 2),
            'best_chunk': {
                'index': best_chunk['chunk_index'],
                'type': best_chunk['chunk_type'],
                'similarity': round(best_chunk['similarity_score'], 2),
                'preview': best_chunk['preview']
            },
            'all_chunks': [
                {
                    'index': c['chunk_index'],
                    'type': c['chunk_type'],
                    'similarity': round(c['similarity_score'], 2)
                }
                for c in sorted(chunk_scores, key=lambda x: x['similarity_score'], reverse=True)[:5]
            ],
            'threshold': self.best_chunk_min,
            'decision': decision,
            'reason': reason,
            'next_stage': next_stage
        }

    def _chunk_cv(self, cv_text: str) -> List[Dict]:
        """Chunk CV by sections or sliding window"""
        section_chunks = self._chunk_by_sections(cv_text)
        
        if len(section_chunks) > 1:
            return section_chunks
        
        return self._chunk_by_sliding_window(cv_text)

    def _chunk_by_sections(self, cv_text: str) -> List[Dict]:
        """Split CV by detected section headers"""
        section_patterns = [
            r'\n\s*(professional\s+)?experience\s*[:\n]',
            r'\n\s*work\s+history\s*[:\n]',
            r'\n\s*(technical\s+)?skills\s*[:\n]',
            r'\n\s*education\s*[:\n]',
            r'\n\s*projects\s*[:\n]',
            r'\n\s*certifications?\s*[:\n]',
            r'\n\s*summary\s*[:\n]',
            r'\n\s*objective\s*[:\n]'
        ]
        
        sections = []
        for pattern in section_patterns:
            for match in re.finditer(pattern, cv_text, re.IGNORECASE):
                section_name = match.group(0).strip().strip(':').strip()
                sections.append((match.start(), section_name))
        
        if not sections:
            return []
        
        sections.sort(key=lambda x: x[0])
        
        chunks = []
        for i, (start_pos, section_name) in enumerate(sections):
            end_pos = sections[i + 1][0] if i < len(sections) - 1 else len(cv_text)
            section_text = cv_text[start_pos:end_pos].strip()
            
            if len(section_text) > 50:
                chunks.append({
                    'type': f'section_{section_name.lower().replace(" ", "_")}',
                    'text': section_text
                })
        
        return chunks

    def _chunk_by_sliding_window(self, cv_text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        """Create overlapping chunks of fixed size"""
        text_length = len(cv_text)
        
        if text_length <= chunk_size:
            return [{'type': 'full_cv', 'text': cv_text}]
        
        chunks = []
        start = 0
        chunk_num = 0
        
        while start < text_length:
            end = start + chunk_size
            
            if end < text_length:
                paragraph_break = cv_text[end:end+100].find('\n\n')
                if paragraph_break != -1:
                    end = end + paragraph_break
            
            chunk_text = cv_text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'type': f'chunk_{chunk_num}',
                    'text': chunk_text
                })
            
            chunk_num += 1
            start = end - overlap
        
        return chunks

    def _extract_persona_requirements(self, persona: Dict) -> str:
        """
        Extract Technical Skills and Education/Experience from persona with fallbacks.
        
        Priority:
        1. Categories named 'Technical Skills' and 'Education and Experience'
        2. If not found, use position 1 and position 6 categories
        3. If still empty, use all categories as fallback
        """
        role_name = persona.get('role_name', persona.get('name', 'Position'))
        parts = [f"Job Role: {role_name}"]
        
        categories = persona.get('categories', [])
        if not categories:
            return '\n'.join(parts)
        
        # Try: Find by exact category names
        target_names = ['Technical Skills', 'Education and Experience']
        # target_names = ['Technical Skills']
        matched_categories = [cat for cat in categories if cat.get('name') in target_names]
        
        # Fallback 1: Use position 1 and 6 if names don't match
        if not matched_categories:
            position_map = {cat.get('position'): cat for cat in categories}
            matched_categories = [
                position_map.get(1),
                position_map.get(6)
            ]
            matched_categories = [cat for cat in matched_categories if cat is not None]
        
        # Fallback 2: Use all categories if still nothing found
        if not matched_categories:
            matched_categories = categories
        
        # Extract requirements from matched categories
        for category in matched_categories:
            cat_name = category.get('name', 'Unknown')
            requirements = []
            
            for subcat in category.get('subcategories', []):
                subcat_name = subcat.get('name', '')
                
                if 'skillset' in subcat and 'technologies' in subcat['skillset']:
                    techs = subcat['skillset']['technologies']
                    if techs:
                        requirements.append(f"{subcat_name}: {', '.join(techs)}")
            
            if requirements:
                parts.append(f"\n{cat_name}:")
                parts.extend(f"  - {req}" for req in requirements)
        
        return '\n'.join(parts)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        return dot_product / (norm1 * norm2)
# class SemanticMatcher:
#     """Stage 1: Fast embedding-based pre-filtering (60% threshold)"""

#     def __init__(self, embedding_service: OpenAIEmbeddingService):
#         self.embedding_service = embedding_service
#         self.threshold = 60.0

#     async def calculate_semantic_match(self, cv_text: str, persona: Dict) -> Dict:
#         """Calculate semantic similarity between CV and persona"""
#         print("📊 Stage 1: Embedding-based pre-filtering...")

#         persona_text = self._extract_persona_text(persona)

#         print("   Generating embeddings...")
#         cv_embedding = await self.embedding_service.embed_text(cv_text)
#         persona_embedding = await self.embedding_service.embed_text(persona_text)

#         similarity = self._cosine_similarity(
#             np.array(cv_embedding),
#             np.array(persona_embedding)
#         )

#         similarity_score = similarity * 100

#         if similarity_score < self.threshold:
#             decision = 'REJECT'
#             reason = f"Semantic match too low ({similarity_score:.1f}% < {self.threshold}% threshold)"
#             next_stage = None
#         else:
#             decision = 'PASS_TO_STAGE2'
#             reason = f"Semantic match sufficient ({similarity_score:.1f}% ≥ {self.threshold}%)"
#             next_stage = 'lightweight_screening'

#         return {
#             'stage': 1,
#             'method': 'embedding_similarity',
#             'score': round(similarity_score, 2),
#             'threshold': self.threshold,
#             'decision': decision,
#             'reason': reason,
#             'next_stage': next_stage
#         }

#     def _extract_persona_text(self, persona: Dict) -> str:
#         """Extract role title and skills/technologies grouped by category"""

#         # Start with role title
#         role_name = persona.get('name', 'Position')
#         parts = [f"Role: {role_name}"]

#         # Group requirements by category for better semantic matching
#         for category in persona.get('categories', []):
#             cat_name = category['name']
#             cat_requirements = []

#             for subcat in category.get('subcategories', []):
#                 if 'skillset' in subcat and 'technologies' in subcat['skillset']:
#                     techs = subcat['skillset']['technologies']
#                     cat_requirements.extend(techs)

#             # Add category block if it has requirements
#             if cat_requirements:
#                 # Keep duplicates within category context
#                 parts.append(f"{cat_name}: {', '.join(cat_requirements)}")

#         return '\n'.join(parts)

#     def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
#         dot_product = np.dot(vec1, vec2)
#         norm1 = np.linalg.norm(vec1)
#         norm2 = np.linalg.norm(vec2)
#         return dot_product / (norm1 * norm2)
    
    