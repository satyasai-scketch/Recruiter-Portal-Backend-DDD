import asyncio
from app.services.embedding import OpenAIEmbeddingService
from app.services.vector_storage import PineconeVectorStorageService
from app.core.config import settings

async def test_individual_services():
    print("Testing OpenAI Embedding Service...")
    print(f"API Key: {settings.OPENAI_API_KEY[:10] if settings.OPENAI_API_KEY else 'EMPTY'}")
    
    try:
        embedding_service = OpenAIEmbeddingService(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL
        )
        print("OpenAI service initialized")
        
        # This MUST call OpenAI API
        vector = await embedding_service.embed_text("test")
        print(f"Embedding generated: {len(vector)} dimensions")
        print(f"First 5 values: {vector[:5]}")
    except Exception as e:
        print(f"OpenAI FAILED: {type(e).__name__}: {e}")
    
    print("\n" + "="*50 + "\n")
    
    print("Testing Pinecone Storage Service...")
    print(f"API Key: {settings.PINECONE_API_KEY[:10] if settings.PINECONE_API_KEY else 'EMPTY'}")
    
    try:
        storage_service = PineconeVectorStorageService(
            api_key=settings.PINECONE_API_KEY,
            index_name=settings.VECTOR_INDEX_NAME,
            dimension=settings.EMBEDDING_DIMENSION
        )
        print("Pinecone service initialized")
        
        # This MUST call Pinecone API
        test_vector = [0.1] * 1536
        results = await storage_service.search_similar(
            query_vector=test_vector,
            top_k=1,
            min_score=0.5
        )
        print(f"Search completed: {len(results)} results")
    except Exception as e:
        print(f"Pinecone FAILED: {type(e).__name__}: {e}")

asyncio.run(test_individual_services())