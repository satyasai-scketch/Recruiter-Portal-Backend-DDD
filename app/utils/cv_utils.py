"""
CV processing utilities for fast baseline extraction and file operations.
"""

import hashlib
import json
import re
from typing import Optional, Dict, Any
from pathlib import Path

# Load country phone information from JSON file
def _load_country_phone_info() -> Dict[str, Dict[str, Any]]:
    """Load country phone information from JSON file."""
    try:
        # Get the path to the JSON file relative to this module
        current_dir = Path(__file__).parent
        json_path = current_dir.parent / "data" / "country_phone_codes.json"
        
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Fallback to a minimal set if file is not found or corrupted
        print(f"Warning: Could not load country phone codes from JSON: {e}")
        return {
            '1': {'name': 'US/Canada', 'min_length': 10, 'max_length': 10},
            '91': {'name': 'India', 'min_length': 10, 'max_length': 10},
            '44': {'name': 'UK', 'min_length': 10, 'max_length': 10},
        }

# Load country phone information
COUNTRY_PHONE_INFO = _load_country_phone_info()


def validate_and_format_phone(country_code: str, number: str) -> Optional[str]:
    """
    Validate and format phone number based on country code.
    
    Args:
        country_code: Country code (e.g., '91', '1', '44')
        number: Phone number without country code
        
    Returns:
        Formatted phone number or None if invalid
    """
    # Clean the number (remove spaces, dashes, etc.)
    clean_number = re.sub(r'[-.\s]', '', number)
    
    # Check if country code exists in our database
    if country_code not in COUNTRY_PHONE_INFO:
        # If country code not found, return as-is with country code
        return f"+{country_code} {clean_number}"
    
    country_info = COUNTRY_PHONE_INFO[country_code]
    min_length = country_info['min_length']
    max_length = country_info['max_length']
    
    # Validate number length
    if len(clean_number) < min_length or len(clean_number) > max_length:
        # If length doesn't match expected range, still return but with warning
        return f"+{country_code} {clean_number}"
    
    # Format based on country
    if country_code == '1':  # US/Canada
        if len(clean_number) == 10:
            return f"+1 ({clean_number[:3]}) {clean_number[3:6]}-{clean_number[6:]}"
        else:
            return f"+1 {clean_number}"
    elif country_code == '91':  # India
        return f"+91 {clean_number}"
    elif country_code == '44':  # UK
        return f"+44 {clean_number}"
    elif country_code == '86':  # China
        return f"+86 {clean_number}"
    elif country_code == '81':  # Japan
        return f"+81 {clean_number}"
    else:
        # Generic international format
        return f"+{country_code} {clean_number}"


def compute_file_hash(file_bytes: bytes) -> str:
    """
    Compute SHA256 hash of file bytes for deduplication.
    
    Args:
        file_bytes: Raw file content as bytes
        
    Returns:
        SHA256 hash as hexadecimal string
    """
    return hashlib.sha256(file_bytes).hexdigest()


def extract_file_extension(filename: str) -> str:
    """
    Extract file extension from filename.
    
    Args:
        filename: Original filename
        
    Returns:
        File extension (e.g., 'pdf', 'docx') without the dot
    """
    return Path(filename).suffix.lstrip('.').lower()


def get_mime_type_from_extension(extension: str) -> Optional[str]:
    """
    Get MIME type from file extension.
    
    Args:
        extension: File extension without dot
        
    Returns:
        MIME type string or None if unknown
    """
    mime_types = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain',
        'rtf': 'application/rtf',
    }
    return mime_types.get(extension.lower())


def extract_baseline_info(text: str) -> Dict[str, Any]:
    """
    Fast baseline extraction of name, email, and phone from CV text.
    Uses regex patterns for speed - no heavy parsing.
    
    Args:
        text: Raw CV text content
        
    Returns:
        Dictionary with extracted information:
        - name: First likely name found (or None)
        - email: First email found (or None) 
        - phone: First phone found (or None)
    """
    # Email regex - more permissive for CVs
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Phone regex - comprehensive international phone number patterns
    # Pattern 1: International format with country code (supports 1-4 digit country codes)
    international_pattern = r'\+(\d{1,4})[-.\s]?(\d{4,20})'
    # Pattern 2: US format (XXX) XXX-XXXX or XXX-XXX-XXXX
    us_pattern = r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    # Pattern 3: General phone pattern (7-15 digits with optional separators)
    general_phone_pattern = r'\b(?:\+?(\d{1,4})[-.\s]?)?(\d{7,15})\b'
    
    # Name pattern - looks for capitalized words at start of lines
    name_pattern = r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    
    result = {
        'name': None,
        'email': None,
        'phone': None
    }
    
    # Extract email
    email_match = re.search(email_pattern, text)
    if email_match:
        result['email'] = email_match.group().lower().strip()
    
    # Extract phone - try different patterns in order of preference
    phone = None
    
    # Try international format first (e.g., +91 9876543210)
    international_match = re.search(international_pattern, text)
    if international_match:
        country_code = international_match.group(1)
        number = international_match.group(2)
        phone = validate_and_format_phone(country_code, number)
    
    # Try US format if no international match found
    if not phone:
        us_match = re.search(us_pattern, text)
        if us_match:
            # Format as (XXX) XXX-XXXX
            phone = f"({us_match.group(1)}) {us_match.group(2)}-{us_match.group(3)}"
    
    # Try general phone pattern for numbers without country code
    if not phone:
        general_match = re.search(general_phone_pattern, text)
        if general_match:
            country_code = general_match.group(1)
            number = general_match.group(2)
            
            if country_code:
                # Has country code
                phone = validate_and_format_phone(country_code, number)
            else:
                # No country code - try to guess based on number length and patterns
                if len(number) == 10 and number.startswith(('6', '7', '8', '9')):
                    # Likely Indian number
                    phone = f"+91 {number}"
                elif len(number) == 10 and number.startswith(('2', '3', '4', '5')):
                    # Could be US number
                    phone = f"+1 ({number[:3]}) {number[3:6]}-{number[6:]}"
                else:
                    # Generic format
                    phone = number
    
    if phone:
        result['phone'] = phone
    
    # Extract name - look at first few lines
    lines = text.split('\n')[:5]  # Check first 5 lines
    for line in lines:
        line = line.strip()
        if len(line) > 3 and len(line) < 50:  # Reasonable name length
            name_match = re.match(name_pattern, line)
            if name_match:
                potential_name = name_match.group(1).strip()
                # Skip if it looks like a header or contains common non-name words
                skip_words = {'resume', 'cv', 'curriculum', 'vitae', 'profile', 'contact', 'personal'}
                if not any(word in potential_name.lower() for word in skip_words):
                    result['name'] = potential_name
                    break
    
    return result


def validate_cv_file(filename: str, file_size: int, max_size_mb: int = 10) -> Dict[str, Any]:
    """
    Validate CV file before processing.
    
    Args:
        filename: Original filename
        file_size: File size in bytes
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        Dictionary with validation result:
        - valid: Boolean indicating if file is valid
        - error: Error message if invalid (or None)
        - extension: File extension
        - mime_type: MIME type
    """
    result = {
        'valid': True,
        'error': None,
        'extension': None,
        'mime_type': None
    }
    
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        result['valid'] = False
        result['error'] = f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
        return result
    
    # Check file extension
    extension = extract_file_extension(filename)
    if not extension:
        result['valid'] = False
        result['error'] = "No file extension found"
        return result
    
    # Check if extension is supported
    supported_extensions = {'pdf', 'doc', 'docx', 'txt', 'rtf'}
    if extension not in supported_extensions:
        result['valid'] = False
        result['error'] = f"Unsupported file type: {extension}. Supported types: {', '.join(supported_extensions)}"
        return result
    
    result['extension'] = extension
    result['mime_type'] = get_mime_type_from_extension(extension)
    
    return result


def generate_s3_key(file_hash: str, extension: str) -> str:
    """
    Generate S3 key for CV file storage.
    Format: cvs/<sha256>.<ext>
    
    Args:
        file_hash: SHA256 hash of the file
        extension: File extension without dot
        
    Returns:
        S3 key string
    """
    return f"cvs/{file_hash}.{extension}"
