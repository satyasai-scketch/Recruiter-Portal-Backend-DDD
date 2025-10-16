#!/usr/bin/env python3
"""
Simple test script to verify CV upload logic with deduplication and versioning.
Run this after setting up the database and S3 configuration.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import get_session
from app.cqrs.handlers import handle_command
from app.cqrs.commands.upload_cv_file import UploadCVFile
from app.utils.cv_utils import compute_file_hash
from unittest.mock import patch, MagicMock


def test_cv_upload():
    """Test CV upload with deduplication and versioning."""
    
    # Sample file content (simulating a CV)
    sample_cv_content = b"""
    John Doe
    Software Engineer
    john.doe@email.com
    (555) 123-4567
    
    Experience:
    - 5 years of Python development
    - 3 years of React experience
    - Team leadership skills
    """
    
    filename = "john_doe_cv.pdf"
    candidate_info = {
        "full_name": "John Doe",
        "email": "john.doe@email.com",
        "phone": "(555) 123-4567"
    }
    
    print("Testing CV Upload Logic")
    print("=" * 50)
    
    # Get database session
    db = get_session()
    
    # Mock storage upload if not configured
    def mock_storage_upload(file_bytes, key, content_type=None, metadata=None):
        return {
            'success': True,
            'url': f'http://localhost:8000/uploads/{key}',
            'error': None
        }
    
    try:
        # Test 1: Upload new CV
        print("\n1. Testing new CV upload...")
        command1 = UploadCVFile(
            file_bytes=sample_cv_content,
            filename=filename,
            candidate_info=candidate_info
        )
        
        # Mock storage upload if not configured
        with patch('app.services.storage.factory.StorageFactory.get_storage_service') as mock_factory:
            mock_service = MagicMock()
            mock_service.upload_file.side_effect = mock_storage_upload
            mock_factory.return_value = mock_service
            result1 = handle_command(db, command1)
        print(f"Result: {result1}")
        
        if result1["status"] == "success":
            print("✅ New CV uploaded successfully")
            print(f"   Candidate ID: {result1['candidate_id']}")
            print(f"   CV ID: {result1['cv_id']}")
            print(f"   Version: {result1['version']}")
            print(f"   File Hash: {result1['file_hash']}")
        else:
            print(f"❌ Upload failed: {result1.get('error', 'Unknown error')}")
            return
        
        # Test 2: Upload same file again (should be duplicate)
        print("\n2. Testing duplicate file upload...")
        command2 = UploadCVFile(
            file_bytes=sample_cv_content,
            filename=filename,
            candidate_info=candidate_info
        )
        
        with patch('app.services.storage.factory.StorageFactory.get_storage_service') as mock_factory:
            mock_service = MagicMock()
            mock_service.upload_file.side_effect = mock_storage_upload
            mock_factory.return_value = mock_service
            result2 = handle_command(db, command2)
        print(f"Result: {result2}")
        
        if result2["status"] == "duplicate":
            print("✅ Duplicate detection working correctly")
            print(f"   Same file hash: {result2['file_hash']}")
            print(f"   Same candidate ID: {result2['candidate_id']}")
        else:
            print(f"❌ Duplicate detection failed: {result2}")
        
        # Test 3: Upload different file for same candidate (should increment version)
        print("\n3. Testing version increment...")
        sample_cv_content_v2 = b"""
        John Doe
        Senior Software Engineer
        john.doe@email.com
        (555) 123-4567
        
        Experience:
        - 6 years of Python development
        - 4 years of React experience
        - Team leadership skills
        - New project management experience
        """
        
        command3 = UploadCVFile(
            file_bytes=sample_cv_content_v2,
            filename="john_doe_cv_v2.pdf",
            candidate_info=candidate_info
        )
        
        with patch('app.services.storage.factory.StorageFactory.get_storage_service') as mock_factory:
            mock_service = MagicMock()
            mock_service.upload_file.side_effect = mock_storage_upload
            mock_factory.return_value = mock_service
            result3 = handle_command(db, command3)
        print(f"Result: {result3}")
        
        if result3["status"] == "success" and result3["version"] == 2:
            print("✅ Version increment working correctly")
            print(f"   New version: {result3['version']}")
            print(f"   Same candidate ID: {result3['candidate_id']}")
        else:
            print(f"❌ Version increment failed: {result3}")
        
        # Test 4: Upload file for different candidate
        print("\n4. Testing different candidate...")
        different_candidate_info = {
            "full_name": "Jane Smith",
            "email": "jane.smith@email.com",
            "phone": "(555) 987-6543"
        }
        
        command4 = UploadCVFile(
            file_bytes=sample_cv_content,
            filename="jane_smith_cv.pdf",
            candidate_info=different_candidate_info
        )
        
        with patch('app.services.storage.factory.StorageFactory.get_storage_service') as mock_factory:
            mock_service = MagicMock()
            mock_service.upload_file.side_effect = mock_storage_upload
            mock_factory.return_value = mock_service
            result4 = handle_command(db, command4)
        print(f"Result: {result4}")
        
        if result4["status"] == "success":
            print("✅ Different candidate created successfully")
            print(f"   New candidate ID: {result4['candidate_id']}")
            print(f"   Version: {result4['version']}")
        else:
            print(f"❌ Different candidate creation failed: {result4}")
        
        print("\n" + "=" * 50)
        print("Test Summary:")
        print(f"- New CV upload: {'✅' if result1['status'] == 'success' else '❌'}")
        print(f"- Duplicate detection: {'✅' if result2['status'] == 'duplicate' else '❌'}")
        print(f"- Version increment: {'✅' if result3['status'] == 'success' and result3['version'] == 2 else '❌'}")
        print(f"- Different candidate: {'✅' if result4['status'] == 'success' else '❌'}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    # Check if S3 is configured
    from app.core.config import settings
    
    if settings.STORAGE_TYPE.lower() == "local":
        print("ℹ️  Info: Using local storage for testing.")
        print("   Set STORAGE_TYPE=s3 in your .env file to test S3 storage.")
    else:
        print("ℹ️  Info: Using S3 storage for testing.")
        print("   Set STORAGE_TYPE=local in your .env file to test local storage.")
    
    test_cv_upload()
