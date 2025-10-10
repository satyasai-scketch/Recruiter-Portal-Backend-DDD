"""
CV processing utilities for fast baseline extraction and file operations.
"""

import hashlib
import re
from typing import Optional, Dict, Any
from pathlib import Path


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
    
    # Phone regex - handles various formats
    phone_pattern = r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    
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
    
    # Extract phone
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        # Format as (XXX) XXX-XXXX
        phone = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
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
