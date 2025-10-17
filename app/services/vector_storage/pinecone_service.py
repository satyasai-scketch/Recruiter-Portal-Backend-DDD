import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pinecone import Pinecone, ServerlessSpec
from .base import VectorStorageService

class PineconeVectorStorageService(VectorStorageService):
    """Pinecone + JSON file dual storage implementation"""
    
    def __init__(self, api_key: str, index_name: str, 
                 dimension: int = 1536,
                 storage_file: str = "data/storage/jd_storage.json",
                 cloud: str = "aws",
                 region: str = "us-east-1"):
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.dimension = dimension
        self.storage_file = storage_file
        self.cloud = cloud
        self.region = region
        
        self._setup_storage()
        self.index = self.pc.Index(index_name)
    
    def _setup_storage(self):
        """Setup Pinecone index and JSON storage"""
        # Create storage directory
        storage_dir = os.path.dirname(self.storage_file)
        if storage_dir:  # Only create directory if there's a valid directory path
            os.makedirs(storage_dir, exist_ok=True)
        
        # Create JSON file if doesn't exist
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        
        # Setup Pinecone index
        existing = [idx.name for idx in self.pc.list_indexes()]
        if self.index_name not in existing:
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=self.cloud, region=self.region)
            )
            import time
            time.sleep(10)  # Wait for index to be ready
    
    async def store_vector(self, doc_id: str, vector: List[float], 
                          metadata: Dict, content: Dict) -> bool:
        """Store vector in Pinecone and complete content in JSON"""
        try:
            # Store complete content in JSON
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                storage = json.load(f)
            
            storage[doc_id] = {
                'content': content,
                'stored_at': datetime.utcnow().isoformat()
            }
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(storage, f, indent=2, ensure_ascii=False)
            
            # Store vector in Pinecone
            self.index.upsert([{
                'id': doc_id,
                'values': vector,
                'metadata': metadata
            }])
            
            return True
        except Exception as e:
            print(f"Storage error: {e}")
            return False
    
    async def search_similar(self, query_vector: List[float], 
                           top_k: int = 5, min_score: float = 0.7,
                           filters: Optional[Dict] = None) -> List[Dict]:
        """Search for similar vectors"""
        try:
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filters
            )
            
            matches = []
            for match in results.matches:
                if match.score >= min_score:
                    matches.append({
                        'id': match.id,
                        'score': round(match.score, 4),
                        'metadata': match.metadata
                    })
            
            return matches
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve complete document from JSON storage"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                storage = json.load(f)
            return storage.get(doc_id, {}).get('content')
        except Exception as e:
            print(f"Retrieval error: {e}")
            return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete from both Pinecone and JSON storage"""
        try:
            # Delete from Pinecone
            self.index.delete(ids=[doc_id])
            
            # Delete from JSON storage
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                storage = json.load(f)
            
            if doc_id in storage:
                del storage[doc_id]
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(storage, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Delete error: {e}")
            return False