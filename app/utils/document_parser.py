"""
Document parsing utilities for extracting text from PDF and DOCX files.
"""

import io
import logging
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import PyPDF2
    import docx
    from docx import Document
except ImportError:
    PyPDF2 = None
    docx = None
    Document = None

logger = logging.getLogger(__name__)


class DocumentParseError(Exception):
    """Raised when document parsing fails."""
    pass


class DocumentParser:
    """Utility class for parsing various document formats."""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def is_supported_format(cls, filename: str) -> bool:
        """Check if the file format is supported."""
        if not filename:
            return False
        extension = Path(filename).suffix.lower()
        return extension in cls.SUPPORTED_EXTENSIONS
    
    @classmethod
    def validate_file_size(cls, file_size: int) -> bool:
        """Validate file size is within limits."""
        return file_size <= cls.MAX_FILE_SIZE
    
    @classmethod
    def extract_text_from_pdf(cls, file_content: bytes) -> str:
        """Extract text from PDF file content."""
        if not PyPDF2:
            raise DocumentParseError("PyPDF2 is not installed. Install with: pip install PyPDF2")
        
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
            
            if not text_content:
                raise DocumentParseError("No text content found in PDF")
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            raise DocumentParseError(f"Failed to parse PDF: {str(e)}")
    
    @classmethod
    def extract_text_from_docx(cls, file_content: bytes) -> str:
        """Extract text from DOCX file content."""
        if not docx:
            raise DocumentParseError("python-docx is not installed. Install with: pip install python-docx")
        
        try:
            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_content.append(" | ".join(row_text))
            
            if not text_content:
                raise DocumentParseError("No text content found in DOCX")
            
            return "\n".join(text_content)
            
        except Exception as e:
            raise DocumentParseError(f"Failed to parse DOCX: {str(e)}")
    
    @classmethod
    def extract_text(cls, filename: str, file_content: bytes) -> Dict[str, Any]:
        """
        Extract text from document file.
        
        Returns:
            Dict containing extracted text and metadata
        """
        if not cls.is_supported_format(filename):
            raise DocumentParseError(f"Unsupported file format: {filename}")
        
        if not cls.validate_file_size(len(file_content)):
            raise DocumentParseError(f"File size exceeds maximum limit of {cls.MAX_FILE_SIZE} bytes")
        
        extension = Path(filename).suffix.lower()
        
        try:
            if extension == '.pdf':
                extracted_text = cls.extract_text_from_pdf(file_content)
            elif extension in ['.docx', '.doc']:
                extracted_text = cls.extract_text_from_docx(file_content)
            else:
                raise DocumentParseError(f"Unsupported file format: {extension}")
            
            return {
                'extracted_text': extracted_text.strip(),
                'original_filename': filename,
                'file_size': len(file_content),
                'file_extension': extension,
                'word_count': len(extracted_text.split()),
                'character_count': len(extracted_text)
            }
            
        except Exception as e:
            if isinstance(e, DocumentParseError):
                raise
            raise DocumentParseError(f"Failed to extract text from {filename}: {str(e)}")


def extract_job_description_text(filename: str, file_content: bytes) -> Dict[str, Any]:
    """
    Convenience function to extract text from job description documents.
    
    Args:
        filename: Name of the uploaded file
        file_content: Binary content of the file
        
    Returns:
        Dict containing extracted text and metadata
        
    Raises:
        DocumentParseError: If parsing fails
    """
    return DocumentParser.extract_text(filename, file_content)
