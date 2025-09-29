from typing import Dict, Any, List
import hashlib

class JDVectorizer:
    """Core JD vectorization logic"""
    
    @staticmethod
    def extract_searchable_text(jd_data: Dict[str, Any]) -> str:
        """Recursively extract all text from JD for vectorization"""
        text_parts = []
        
        def extract_recursive(obj, parent_key=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key not in ['id', 'created_at', 'updated_at']:
                        extract_recursive(value, key)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item, parent_key)
            elif isinstance(obj, str) and obj.strip():
                if parent_key:
                    text_parts.append(f"{parent_key}: {obj.strip()}")
                else:
                    text_parts.append(obj.strip())
            elif isinstance(obj, (int, float)):
                text_parts.append(str(obj))
        
        extract_recursive(jd_data)
        return " | ".join(text_parts)
    
    @staticmethod
    def generate_id(jd_data: Dict[str, Any]) -> str:
        """Generate unique ID for JD"""
        if 'id' in jd_data:
            return str(jd_data['id'])
        
        text = JDVectorizer.extract_searchable_text(jd_data)
        return f"jd_{hashlib.md5(text.encode()).hexdigest()[:12]}"
    
    @staticmethod
    def extract_metadata(jd_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract filterable metadata from JD"""
        metadata = {}
        
        # Extract common fields if they exist
        for field in ['title', 'domain', 'level', 'family', 'location', 'type']:
            if field in jd_data:
                value = str(jd_data[field])[:100]
                if value.strip():
                    metadata[field] = value
        
        metadata['content_length'] = str(len(str(jd_data)))
        return metadata