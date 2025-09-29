from typing import Dict, Any, List, Optional, Union
from app.services.embedding import EmbeddingService, OpenAIEmbeddingService
from app.services.vector_storage import VectorStorageService, PineconeVectorStorageService
from app.core.config import settings
from .vectorizer import JDVectorizer

class JDTemplateService:
    """
    High-level service for JD template management.
    This is the main interface that should be used by other parts of the application.
    """
    
    def __init__(self, 
                 embedding_service: Optional[EmbeddingService] = None,
                 storage_service: Optional[VectorStorageService] = None):
        """
        Initialize with optional custom services (dependency injection).
        If not provided, uses default implementations from config.
        """
        self.embedding_service = embedding_service or OpenAIEmbeddingService(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL
        )
        
        self.storage_service = storage_service or PineconeVectorStorageService(
            api_key=settings.PINECONE_API_KEY,
            index_name=settings.VECTOR_INDEX_NAME,
            dimension=settings.EMBEDDING_DIMENSION,
            storage_file=settings.JD_STORAGE_FILE,
            cloud=settings.PINECONE_CLOUD,
            region=settings.PINECONE_REGION
        )
    
    async def add_template(self, jd_data: Dict[str, Any]) -> bool:
        """
        Add a single JD template to vector storage.
        
        Args:
            jd_data: Complete JD data (any structure)
            
        Returns:
            bool: True if successfully stored, False otherwise
        """
        try:
            # Extract searchable text
            text = JDVectorizer.extract_searchable_text(jd_data)
            if not text.strip():
                print(f"No searchable content in JD")
                return False
            
            # Generate ID and metadata
            jd_id = JDVectorizer.generate_id(jd_data)
            metadata = JDVectorizer.extract_metadata(jd_data)
            
            # Generate embedding
            vector = await self.embedding_service.embed_text(text)
            
            # Store vector + complete data
            success = await self.storage_service.store_vector(
                doc_id=jd_id,
                vector=vector,
                metadata=metadata,
                content=jd_data
            )
            
            if success:
                title = jd_data.get('title', 'Untitled')
                print(f"Stored template: {title} (ID: {jd_id})")
            
            return success
            
        except Exception as e:
            print(f"Error adding template: {e}")
            return False
    
    async def find_best_match(self, user_jd_input: Union[str, Dict[str, Any]], 
                         min_similarity: float = 0.5) -> Optional[Dict[str, Any]]:
        """
        Find the single best matching template for a user's JD.
        
        Args:
            user_jd_input: User's JD as plain text string OR structured dict
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            Complete JD template dict with ALL fields (whatever exists in the template)
            Returns None if no match found
        """
        try:
            # Handle both text and dict input
            if isinstance(user_jd_input, str):
                # Plain text input - use directly for vectorization
                query_text = user_jd_input
            elif isinstance(user_jd_input, dict):
                # Structured dict - extract all text
                query_text = JDVectorizer.extract_searchable_text(user_jd_input)
            else:
                print(f"Invalid input type: {type(user_jd_input)}")
                return None
            
            if not query_text.strip():
                print("Empty query text provided")
                return None
            
            # Vectorize query
            query_vector = await self.embedding_service.embed_text(query_text)
            
            # Search for best match
            matches = await self.storage_service.search_similar(
                query_vector=query_vector,
                top_k=1,
                min_score=min_similarity
            )
            
            if not matches:
                print(f"No matches found above similarity threshold {min_similarity}")
                return None
            
            # Get complete template data (returns entire dict with all fields)
            best_match_id = matches[0]['id']
            complete_template = await self.storage_service.get_document(best_match_id)
            
            if complete_template:
                similarity = matches[0]['score']
                title = complete_template.get('title', 'Untitled')
                print(f"Best match: {title} (similarity: {similarity})")
            
            # Returns the COMPLETE template dict - no need to access .title, .skills
            # All fields are available in the returned dict
            return complete_template
            
        except Exception as e:
            print(f"Error finding best match: {e}")
            return None
    
    async def find_top_matches(self, user_jd_input: Union[str, Dict[str, Any]], 
                          top_k: int = 5,
                          min_similarity: float = 0.5) -> List[Dict[str, Any]]:
        """
        Find top K matching templates.
        
        Args:
            user_jd_input: User's JD as plain text string OR structured dict
            top_k: Number of matches to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of dicts with 'template' (complete dict), 'similarity', and 'id' keys
        """
        try:
            # Handle both text and dict input
            if isinstance(user_jd_input, str):
                query_text = user_jd_input
            elif isinstance(user_jd_input, dict):
                query_text = JDVectorizer.extract_searchable_text(user_jd_input)
            else:
                print(f"Invalid input type: {type(user_jd_input)}")
                return []
            
            if not query_text.strip():
                return []
            
            # Vectorize and search
            query_vector = await self.embedding_service.embed_text(query_text)
            matches = await self.storage_service.search_similar(
                query_vector=query_vector,
                top_k=top_k,
                min_score=min_similarity
            )
            
            # Get complete template data for each match
            results = []
            for match in matches:
                template = await self.storage_service.get_document(match['id'])
                if template:
                    results.append({
                        'template': template,  # Complete dict with all fields
                        'similarity': match['score'],
                        'id': match['id']
                    })
            
            return results
            
        except Exception as e:
            print(f"Error finding top matches: {e}")
            return []