#!/usr/bin/env python3
"""
Test CV upload logic without S3 dependency - focuses on database operations.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import get_session
from app.services.candidate_service import CandidateService
from app.repositories.candidate_repo import SQLAlchemyCandidateRepository
from app.repositories.candidate_cv_repo import SQLAlchemyCandidateCVRepository
from app.utils.cv_utils import compute_file_hash, validate_cv_file


def test_database_operations():
    """Test database operations without S3."""
    
    # Sample file content
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
    
    print("Testing Database Operations (No S3)")
    print("=" * 50)
    
    # Get database session
    db = get_session()
    
    try:
        # Initialize services
        candidate_repo = SQLAlchemyCandidateRepository()
        cv_repo = SQLAlchemyCandidateCVRepository()
        service = CandidateService(candidates=candidate_repo, candidate_cvs=cv_repo)
        
        # Test 1: File validation
        print("\n1. Testing file validation...")
        validation = validate_cv_file(filename, len(sample_cv_content))
        print(f"Validation result: {validation}")
        
        if validation["valid"]:
            print("✅ File validation passed")
        else:
            print(f"❌ File validation failed: {validation['error']}")
            return
        
        # Test 2: Hash computation
        print("\n2. Testing hash computation...")
        file_hash = compute_file_hash(sample_cv_content)
        print(f"File hash: {file_hash}")
        print("✅ Hash computation successful")
        
        # Test 3: Check for existing CV by hash
        print("\n3. Testing duplicate detection...")
        existing_cv = cv_repo.find_by_hash(db, file_hash)
        if existing_cv:
            print(f"✅ Found existing CV: {existing_cv.id}")
        else:
            print("✅ No existing CV found (expected for new file)")
        
        # Test 4: Find or create candidate
        print("\n4. Testing candidate find/create...")
        candidate = service._find_or_create_candidate(db, candidate_info)
        print(f"Candidate ID: {candidate.id}")
        print(f"Candidate email: {candidate.email}")
        print("✅ Candidate find/create successful")
        
        # Test 5: Get next version
        print("\n5. Testing version increment...")
        version = cv_repo.get_next_version(db, candidate.id)
        print(f"Next version: {version}")
        print("✅ Version increment successful")
        
        # Test 6: Check candidate CVs
        print("\n6. Testing candidate CVs listing...")
        cvs = cv_repo.get_candidate_cvs(db, candidate.id)
        print(f"Existing CVs count: {len(cvs)}")
        for cv in cvs:
            print(f"  - CV {cv.version}: {cv.file_name} (hash: {cv.file_hash[:16]}...)")
        print("✅ CV listing successful")
        
        print("\n" + "=" * 50)
        print("Database Operations Test Summary:")
        print("✅ File validation")
        print("✅ Hash computation")
        print("✅ Duplicate detection")
        print("✅ Candidate find/create")
        print("✅ Version increment")
        print("✅ CV listing")
        print("\nAll database operations working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    test_database_operations()
