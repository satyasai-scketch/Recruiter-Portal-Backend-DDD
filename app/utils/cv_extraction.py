"""
CV extraction utilities with multiple approaches and performance analysis.
Supports regex, SpaCy, LLM, and parser-based extraction methods.
"""

import time
import re
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

try:
    import spacy
    from spacy import displacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from app.core.config import settings
from app.utils.cv_utils import extract_baseline_info as regex_extract_baseline_info


@dataclass
class ExtractionResult:
    """Result of CV extraction with timing information."""
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    approach: str
    processing_time_ms: float
    success: bool
    error: Optional[str] = None


class CVExtractor:
    """CV extraction with multiple approaches and performance tracking."""
    
    def __init__(self):
        self.spacy_model = None
        self.groq_client = None
        self._load_spacy_model()
        self._load_groq_client()
    
    def _load_spacy_model(self):
        """Load SpaCy model if available."""
        if not SPACY_AVAILABLE:
            return
        
        try:
            # Try to load the English model
            self.spacy_model = spacy.load("en_core_web_sm")
        except OSError:
            try:
                # Fallback to smaller model
                self.spacy_model = spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: SpaCy English model not found. Install with: python -m spacy download en_core_web_sm")
                self.spacy_model = None
    
    def _load_groq_client(self):
        """Load Groq client if available and configured."""
        if not GROQ_AVAILABLE:
            return
        
        if not settings.GROQ_API_KEY:
            print("Warning: GROQ_API_KEY not configured. LLM extraction will not be available.")
            return
        
        try:
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        except Exception as e:
            print(f"Warning: Failed to initialize Groq client: {e}")
            self.groq_client = None
    
    def extract_baseline_info(self, text: str, approach: Optional[str] = None) -> ExtractionResult:
        """
        Extract baseline info (name, email, phone) using specified approach.
        
        Args:
            text: CV text content
            approach: Extraction approach ("regex", "spacy", "llm", "parser")
                     If None, uses the configured approach from settings
            
        Returns:
            ExtractionResult with extracted data and timing information
        """
        if approach is None:
            approach = settings.CV_EXTRACTION_APPROACH
        
        start_time = time.time()
        
        try:
            if approach == "regex":
                result = self._extract_with_regex(text)
            elif approach == "spacy":
                result = self._extract_with_spacy(text)
            elif approach == "llm":
                result = self._extract_with_llm(text)
            elif approach == "parser":
                result = self._extract_with_parser(text)
            else:
                raise ValueError(f"Unknown extraction approach: {approach}")
            
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return ExtractionResult(
                name=result.get("name"),
                email=result.get("email"),
                phone=result.get("phone"),
                approach=approach,
                processing_time_ms=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return ExtractionResult(
                name=None,
                email=None,
                phone=None,
                approach=approach,
                processing_time_ms=processing_time,
                success=False,
                error=str(e)
            )
    
    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """Extract using regex patterns (current baseline approach)."""
        return regex_extract_baseline_info(text)
    
    def _extract_with_spacy(self, text: str) -> Dict[str, Any]:
        """Extract using SpaCy NLP model."""
        if not SPACY_AVAILABLE or not self.spacy_model:
            raise RuntimeError("SpaCy not available or model not loaded")
        
        result = {
            'name': None,
            'email': None,
            'phone': None
        }
        
        # Process text with SpaCy
        doc = self.spacy_model(text)
        
        # Extract email using regex (SpaCy doesn't have built-in email recognition)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            result['email'] = email_match.group().lower().strip()
        
        # Extract phone using regex (SpaCy doesn't have built-in phone recognition)
        phone_patterns = [
            r'\+(\d{1,4})[-.\s]?(\d{4,20})',  # International format
            r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # US format
            r'\b(?:\+?(\d{1,4})[-.\s]?)?(\d{7,15})\b'  # General format
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                if len(phone_match.groups()) >= 2:
                    country_code = phone_match.group(1) or ""
                    number = phone_match.group(2)
                    if country_code:
                        result['phone'] = f"+{country_code} {number}"
                    else:
                        result['phone'] = number
                else:
                    result['phone'] = phone_match.group()
                break
        
        # Extract name using improved logic
        # First, try to find PERSON entities in the first few lines (not sentences)
        lines = text.split('\n')[:5]  # Check first 5 lines
        
        for line in lines:
            line = line.strip()
            if len(line) > 3 and len(line) < 100:  # Reasonable name length
                # Process just this line with SpaCy
                line_doc = self.spacy_model(line)
                
                # Look for PERSON entities in this line
                for ent in line_doc.ents:
                    if ent.label_ == "PERSON":
                        name = ent.text.strip()
                        # Skip if it looks like a header or contains common non-name words
                        skip_words = {'resume', 'cv', 'curriculum', 'vitae', 'profile', 'contact', 'personal', 'html', 'css', 'javascript', 'react', 'node', 'python', 'java'}
                        if not any(word in name.lower() for word in skip_words):
                            # Additional validation: check if it looks like a real name
                            if len(name.split()) >= 2 and all(word.isalpha() for word in name.split()):
                                result['name'] = name
                                break
                if result['name']:
                    break
        
        # Fallback: if no PERSON entity found, look for capitalized words at start of lines
        if not result['name']:
            lines = text.split('\n')[:5]
            # Improved pattern to handle names like "AJITESH MISHRA" (all caps)
            name_pattern = r'^([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)'
            
            for line in lines:
                line = line.strip()
                if len(line) > 3 and len(line) < 100:
                    name_match = re.match(name_pattern, line)
                    if name_match:
                        potential_name = name_match.group(1).strip()
                        skip_words = {'resume', 'cv', 'curriculum', 'vitae', 'profile', 'contact', 'personal', 'html', 'css', 'javascript', 'react', 'node', 'python', 'java'}
                        if not any(word in potential_name.lower() for word in skip_words):
                            # Additional validation: should have at least 2 words and be reasonable length
                            if len(potential_name.split()) >= 2 and len(potential_name) <= 50:
                                result['name'] = potential_name
                                break
        
        return result
    
    def _extract_with_llm(self, text: str) -> Dict[str, Any]:
        """Extract using LLM with Groq."""
        if not GROQ_AVAILABLE or not self.groq_client:
            raise RuntimeError("Groq not available or not configured")
        
        # Create a structured prompt for extraction
        prompt = f"""
Extract the following information from this CV/resume text. Return ONLY a JSON object with the exact structure shown below. Do not include any other text or explanation.

CV Text:
{text[:2000]}  # Limit text to avoid token limits

Required JSON format:
{{
    "name": "Full name of the person (or null if not found)",
    "email": "Email address (or null if not found)", 
    "phone": "Phone number (or null if not found)"
}}

Instructions:
- For name: Extract the person's full name, typically found at the top of the CV
- For email: Extract any email address found in the text
- For phone: Extract any phone number found in the text
- If any field is not found, use null
- Return only valid JSON, no additional text
"""

        try:
            # Make API call to Groq
            response = self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured information from CVs and resumes. Always return valid JSON only."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=settings.GROQ_TEMPERATURE,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            import json
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                extracted_data = json.loads(result_text)
                
                # replace spaces with '' in email
                if extracted_data['email']:
                    extracted_data['email'] = extracted_data['email'].replace(' ', '')
                    
                # Validate and clean the extracted data
                result = {
                    'name': self._clean_name(extracted_data.get('name')),
                    'email': self._clean_email(extracted_data.get('email')),
                    'phone': self._clean_phone(extracted_data.get('phone'))
                }
                
                return result
                
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract from the response text
                print(f"Warning: Failed to parse LLM response as JSON: {e}")
                print(f"Response was: {result_text}")
                
                # Fallback: try to extract using regex patterns from the response
                return self._fallback_extract_from_llm_response(result_text)
                
        except Exception as e:
            raise RuntimeError(f"LLM extraction failed: {str(e)}")
    
    def _clean_name(self, name: Any) -> Optional[str]:
        """Clean and validate extracted name."""
        if not name or name == "null" or name == "None":
            return None
        
        name = str(name).strip()
        if len(name) < 2 or len(name) > 100:
            return None
        
        # Skip if it looks like a technical term
        skip_words = {'html', 'css', 'javascript', 'react', 'node', 'python', 'java', 'phone', 'email', 'contact'}
        if any(word in name.lower() for word in skip_words):
            return None
        
        return name
    
    def _clean_email(self, email: Any) -> Optional[str]:
        """Clean and validate extracted email."""
        if not email or email == "null" or email == "None":
            return None
        
        email = str(email).strip().lower()
        
        # Basic email validation
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.match(email_pattern, email):
            return email
        
        return None
    
    def _clean_phone(self, phone: Any) -> Optional[str]:
        """Clean and validate extracted phone."""
        if not phone or phone == "null" or phone == "None":
            return None
        
        phone = str(phone).strip()
        
        # Basic phone validation - should contain digits
        if not any(c.isdigit() for c in phone):
            return None
        
        return phone
    
    def _fallback_extract_from_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Fallback extraction when JSON parsing fails."""
        result = {
            'name': None,
            'email': None,
            'phone': None
        }
        
        # Try to extract using regex patterns
        import re
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, response_text)
        if email_match:
            result['email'] = email_match.group().lower().strip()
        
        # Extract phone
        phone_pattern = r'\+?[\d\s\-\(\)]{7,20}'
        phone_match = re.search(phone_pattern, response_text)
        if phone_match:
            result['phone'] = phone_match.group().strip()
        
        # Extract name (look for quoted strings or capitalized words)
        name_patterns = [
            r'"name":\s*"([^"]+)"',
            r'"name":\s*([^,\n}]+)',
            r'name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, response_text, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
                if len(name) > 2 and len(name) < 100:
                    result['name'] = name
                    break
        
        return result
    
    def _extract_with_parser(self, text: str) -> Dict[str, Any]:
        """Extract using open source CV parsers (placeholder for future implementation)."""
        # This will be implemented in Approach 3
        raise NotImplementedError("Parser extraction not yet implemented")
    
    def compare_approaches(self, text: str, approaches: list = None) -> Dict[str, ExtractionResult]:
        """
        Compare multiple extraction approaches on the same text.
        
        Args:
            text: CV text content
            approaches: List of approaches to compare. If None, compares all available approaches.
            
        Returns:
            Dictionary mapping approach names to ExtractionResult objects
        """
        if approaches is None:
            approaches = ["regex"]
            if SPACY_AVAILABLE and self.spacy_model:
                approaches.append("spacy")
            if GROQ_AVAILABLE and self.groq_client:
                approaches.append("llm")
        
        results = {}
        for approach in approaches:
            try:
                result = self.extract_baseline_info(text, approach)
                results[approach] = result
            except Exception as e:
                results[approach] = ExtractionResult(
                    name=None,
                    email=None,
                    phone=None,
                    approach=approach,
                    processing_time_ms=0.0,
                    success=False,
                    error=str(e)
                )
        
        return results


# Global extractor instance
cv_extractor = CVExtractor()


def extract_baseline_info_with_timing(text: str, approach: Optional[str] = None) -> ExtractionResult:
    """
    Convenience function to extract baseline info with timing.
    
    Args:
        text: CV text content
        approach: Extraction approach. If None, uses configured approach.
        
    Returns:
        ExtractionResult with extracted data and timing information
    """
    return cv_extractor.extract_baseline_info(text, approach)


def compare_extraction_approaches(text: str, approaches: list = None) -> Dict[str, ExtractionResult]:
    """
    Convenience function to compare multiple extraction approaches.
    
    Args:
        text: CV text content
        approaches: List of approaches to compare
        
    Returns:
        Dictionary mapping approach names to ExtractionResult objects
    """
    return cv_extractor.compare_approaches(text, approaches)
