from typing import List, Dict, Optional
from datetime import datetime
from pinecone import Pinecone
from app.core.config import settings

class PineconeV3Service:
    """
    V3 Pinecone service - SIMPLIFIED (no JSON file)
    Only stores vectors + metadata in Pinecone
    JD text fetched from SQL when needed
    """
    
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_V3_INDEX_NAME
        
        # Ensure index exists
        existing = [idx.name for idx in self.pc.list_indexes()]
        if self.index_name not in existing:
            print(f"⚠️  Pinecone index '{self.index_name}' not found!")
            print(f"   Create it in Pinecone dashboard or run setup script")
        
        self.index = self.pc.Index(self.index_name)
    
    async def store_ai_persona(
        self, 
        jd_id: str,
        jd_embedding: List[float],
        ai_persona_id: str,
        metadata: Dict
    ) -> bool:
        """
        Store JD embedding in Pinecone with link to AI persona.
        NO full content storage - we fetch from SQL when needed.
        """
        try:
            vector_id = f"jd_{jd_id}_ai_{ai_persona_id}"
            
            # ONLY small metadata (for filtering/display)
            pinecone_metadata = {
                'jd_id': jd_id,
                'ai_persona_id': ai_persona_id,
                'job_title': metadata.get('job_title', ''),
                'job_family': metadata.get('job_family', ''),
                'seniority': metadata.get('seniority', ''),
                'technical_intensity': metadata.get('technical_intensity', ''),
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Store ONLY in Pinecone
            self.index.upsert([{
                'id': vector_id,
                'values': jd_embedding,
                'metadata': pinecone_metadata
            }])
            
            print(f"   ✅ Cached in Pinecone: {vector_id}")
            return True
            
        except Exception as e:
            print(f"   ❌ Pinecone error: {e}")
            return False
    
    async def find_similar_jds(
        self,
        jd_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.85
    ) -> List[Dict]:
        """Find similar JDs by vector similarity"""
        try:
            results = self.index.query(
                vector=jd_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            similar = []
            for match in results.matches:
                #print(match.score)
                if match.score >= min_similarity:
                    similar.append({
                        'jd_id': match.metadata.get('jd_id'),
                        'ai_persona_id': match.metadata.get('ai_persona_id'),
                        'similarity': round(match.score, 4),
                        'job_title': match.metadata.get('job_title', ''),
                        'job_family': match.metadata.get('job_family', ''),
                        'seniority': match.metadata.get('seniority', ''),
                        'metadata': match.metadata
                    })
            
            return similar
            
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            return []