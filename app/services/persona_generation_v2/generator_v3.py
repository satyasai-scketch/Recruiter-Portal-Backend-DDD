from typing import Dict, Any, List
import time
from sqlalchemy.orm import Session

from app.services.persona_generation_v2 import OpenAIPersonaGeneratorV2
from app.services.persona_generation_v2.persona_adapter import PersonaAdapterService
from app.services.embedding.openai_service import OpenAIEmbeddingService
from app.services.vector_storage.pinecone_service import PineconeVectorStorageService
from app.services.vector_storage.pinecone_v3 import PineconeV3Service
from app.services.llm.OpenAIClient import OpenAIClient
from app.services.ai_persona_service import AIPersonaService
from app.repositories.job_description_repo import SQLAlchemyJobDescriptionRepository
from app.core.config import settings

class OpenAIPersonaGeneratorV3:
    """V3 with AI template caching (doesn't modify V2)"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o", db: Session = None):
        self.api_key = api_key
        self.model = model
        self.db = db
        
        # V2 generator (unchanged)
        self.v2_generator = OpenAIPersonaGeneratorV2(api_key, model)
        
        # V3 services
        self.embedding_service = OpenAIEmbeddingService(api_key)
        self.adapter_service = PersonaAdapterService(OpenAIClient(api_key=api_key), "gpt-4o-mini")
        
        self.vector_store = PineconeV3Service()
        
        self.ai_persona_service = AIPersonaService()
        self.jd_repo = SQLAlchemyJobDescriptionRepository()
    
    async def generate_persona_from_jd(self, jd_text: str, jd_id: str) -> Dict[str, Any]:
        """
        Returns:
        {
            'persona': {...},
            'analysis': {...},  # Only if full pipeline
            'generation_method': 'full_pipeline' | 'adapted',
            'ai_persona_id': 'xxx',
            'source_similarity': 0.92  # Only if adapted
        }
        """
        print(f"\n🎯 V3 Generator for JD: {jd_id}")
        start_time = time.time()
        
        # Embed JD
        print("📊 Embedding...")
        jd_embedding = await self.embedding_service.embed_text(jd_text)
        
        # Search
        print("🔍 Searching similar JDs...")
        similar_jds = await self.vector_store.find_similar_jds(jd_embedding, top_k=3, min_similarity=0.70)
        
        if not similar_jds:
            print("❌ No match - full pipeline")
            return await self._full_pipeline_and_cache(jd_text, jd_id, jd_embedding, start_time)
        
        # Found match - adapt
        best = similar_jds[0]
        print(f"✅ Found! Similarity: {best['similarity']:.2%}")
        
        ai_template = self.ai_persona_service.get_by_id(self.db, best['ai_persona_id'])
        if not ai_template:
            print("⚠️  Template missing - full pipeline")
            return await self._full_pipeline_and_cache(jd_text, jd_id, jd_embedding, start_time)
        
        # Get original JD
        original_jd = self.jd_repo.get(self.db, best['jd_id'])
        if not original_jd:
            print("⚠️  Original JD not found - full pipeline")
            return await self._full_pipeline_and_cache(jd_text, jd_id, jd_embedding, start_time)
        
        # Get text in priority order
        # original_jd_text = (
        #     original_jd.selected_text or 
        #     original_jd.refined_text or 
        #     original_jd.original_text
        # )
        # Adapt
        original_jd_text = ai_template.jd_text
        print(f"🔧 Adapting...")
        adapted = await self.adapter_service.adapt_persona(
            original_jd_text, jd_text, ai_template.persona_json, best['similarity']
        )
        
        print(f"✅ Done in {time.time() - start_time:.2f}s")
        
        return {
            'persona': adapted,
            'generation_method': 'adapted',
            'ai_persona_id': ai_template.id,
            'source_similarity': best['similarity']
        }
    
    async def _full_pipeline_and_cache(
        self, 
        jd_text: str, 
        jd_id: str, 
        jd_embedding: List[float], 
        start_time: float
    ) -> Dict:
        """Run V2 full pipeline and cache result"""
        print("🤖 V2 Full Pipeline...")
        
        # V2 returns persona directly (not wrapped in dict)
        persona = await self.v2_generator.generate_persona_from_jd(jd_text, jd_id)
        
        gen_time = int(time.time() - start_time)
        print(f"✅ Generated in {gen_time}s")
        
        # Extract analysis insights from persona
        # V2 adds this to the persona structure
        analysis_insights = persona.get('analysis_insights', {})
        
        # Build metadata for Pinecone/AI table
        metadata = {
            'job_title': persona.get('name', '').replace(' Persona', ''),  
            'job_family': analysis_insights.get('job_family', ''),
            'seniority': analysis_insights.get('seniority_level', ''),
            'technical_intensity': analysis_insights.get('technical_intensity', '')
        }
        
        # Store in AI template table
        print("💾 Saving to AI template library...")
        ai_persona_data = {
            'job_description_id': jd_id,
            'persona_json': persona,  # Complete persona structure
            'analysis_json': analysis_insights,  # Analysis insights from V2
            'weights_data_json': analysis_insights.get('weight_reasoning', {}),  # Weight reasoning
            'jd_text': jd_text,
            'job_title': metadata['job_title'],
            'job_family': metadata['job_family'],
            'seniority_level': metadata['seniority'],
            'technical_intensity': metadata['technical_intensity'],
            'model_used': self.model,
            'generation_time_seconds': gen_time
        }
        
        try:
            ai_persona = self.ai_persona_service.create(self.db, ai_persona_data)
            print(f"   ✅ Saved AI template: {ai_persona.id}")
        except Exception as e:
            print(f"   ❌ Failed to save AI template: {e}")
            raise
        
        # Cache in Pinecone
        print("💾 Caching in Pinecone...")
        try:
            await self.vector_store.store_ai_persona(
                jd_id=jd_id,
                jd_embedding=jd_embedding,
                ai_persona_id=ai_persona.id,
                metadata=metadata
            )
            print(f"   ✅ Cached in Pinecone")
        except Exception as e:
            print(f"   ❌ Failed to cache in Pinecone: {e}")
            # Don't fail if Pinecone caching fails
        
        # Return in V3 format
        return {
            'persona': persona,
            'analysis': analysis_insights,
            'weights_data': analysis_insights.get('weight_reasoning', {}),
            'generation_method': 'full_pipeline',
            'ai_persona_id': ai_persona.id
        }