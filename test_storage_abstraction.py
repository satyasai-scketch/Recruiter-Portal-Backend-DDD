#!/usr/bin/env python3
"""
Test script for the storage abstraction layer.
Tests both local and S3 storage implementations.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.storage import StorageFactory, LocalStorageService, S3StorageService
from app.core.config import settings


def test_storage_factory():
    """Test the storage factory functionality."""
    
    print("🏭 Testing Storage Factory")
    print("=" * 50)
    
    # Test 1: Get local storage service
    print("\n1. Testing local storage service creation...")
    try:
        local_service = StorageFactory.get_storage_service("local")
        print(f"✅ Local storage service created: {type(local_service).__name__}")
        print(f"   Storage path: {local_service.storage_path}")
        print(f"   URL prefix: {local_service.url_prefix}")
    except Exception as e:
        print(f"❌ Failed to create local storage service: {str(e)}")
    
    # Test 2: Get S3 storage service
    print("\n2. Testing S3 storage service creation...")
    try:
        s3_service = StorageFactory.get_storage_service("s3")
        print(f"✅ S3 storage service created: {type(s3_service).__name__}")
        print(f"   Bucket: {s3_service.bucket_name}")
        print(f"   Region: {s3_service.aws_region}")
    except Exception as e:
        print(f"❌ Failed to create S3 storage service: {str(e)}")
    
    # Test 3: Test configuration validation
    print("\n3. Testing configuration validation...")
    for storage_type in ["local", "s3"]:
        validation = StorageFactory.validate_storage_config(storage_type)
        status = "✅" if validation['valid'] else "❌"
        print(f"   {storage_type}: {status} {validation}")
    
    # Test 4: Test singleton pattern
    print("\n4. Testing singleton pattern...")
    try:
        service1 = StorageFactory.get_singleton_storage_service("local")
        service2 = StorageFactory.get_singleton_storage_service("local")
        if service1 is service2:
            print("✅ Singleton pattern working correctly")
        else:
            print("❌ Singleton pattern not working")
    except Exception as e:
        print(f"❌ Singleton test failed: {str(e)}")


def test_local_storage():
    """Test local storage functionality."""
    
    print("\n\n💾 Testing Local Storage")
    print("=" * 50)
    
    try:
        # Create local storage service
        local_service = LocalStorageService()
        
        # Test file content
        test_content = b"This is a test CV file content for local storage testing."
        test_key = "cvs/test_file.txt"
        
        # Test 1: Upload file
        print("\n1. Testing file upload...")
        upload_result = local_service.upload_file(
            file_bytes=test_content,
            key=test_key,
            content_type="text/plain"
        )
        
        if upload_result['success']:
            print("✅ File upload successful")
            print(f"   URL: {upload_result['url']}")
        else:
            print(f"❌ File upload failed: {upload_result['error']}")
            return
        
        # Test 2: Check if file exists
        print("\n2. Testing file existence check...")
        exists = local_service.file_exists(test_key)
        if exists:
            print("✅ File existence check working")
        else:
            print("❌ File existence check failed")
        
        # Test 3: Get file URL
        print("\n3. Testing URL generation...")
        url = local_service.get_file_url(test_key)
        print(f"   Generated URL: {url}")
        
        # Test 4: Get storage info
        print("\n4. Testing storage info...")
        info = local_service.get_storage_info()
        print(f"   Storage info: {info}")
        
        # Test 5: Delete file
        print("\n5. Testing file deletion...")
        delete_result = local_service.delete_file(test_key)
        if delete_result['success']:
            print("✅ File deletion successful")
        else:
            print(f"❌ File deletion failed: {delete_result['error']}")
        
        # Test 6: Verify file is deleted
        print("\n6. Verifying file deletion...")
        exists_after = local_service.file_exists(test_key)
        if not exists_after:
            print("✅ File successfully deleted")
        else:
            print("❌ File still exists after deletion")
    
    except Exception as e:
        print(f"❌ Local storage test failed: {str(e)}")
        import traceback
        traceback.print_exc()


def test_s3_storage():
    """Test S3 storage functionality (if configured)."""
    
    print("\n\n☁️  Testing S3 Storage")
    print("=" * 50)
    
    # Check if S3 is configured
    if not settings.S3_BUCKET_NAME:
        print("⚠️  S3 not configured. Skipping S3 tests.")
        print("   Set S3_BUCKET_NAME in your .env file to test S3 storage.")
        return
    
    try:
        # Create S3 storage service
        s3_service = S3StorageService()
        
        # Test file content
        test_content = b"This is a test CV file content for S3 storage testing."
        test_key = "cvs/test_file_s3.txt"
        
        # Test 1: Upload file
        print("\n1. Testing S3 file upload...")
        upload_result = s3_service.upload_file(
            file_bytes=test_content,
            key=test_key,
            content_type="text/plain"
        )
        
        if upload_result['success']:
            print("✅ S3 file upload successful")
            print(f"   URL: {upload_result['url']}")
        else:
            print(f"❌ S3 file upload failed: {upload_result['error']}")
            return
        
        # Test 2: Check if file exists
        print("\n2. Testing S3 file existence check...")
        exists = s3_service.file_exists(test_key)
        if exists:
            print("✅ S3 file existence check working")
        else:
            print("❌ S3 file existence check failed")
        
        # Test 3: Get file URL
        print("\n3. Testing S3 URL generation...")
        url = s3_service.get_file_url(test_key)
        print(f"   Generated URL: {url}")
        
        # Test 4: Get storage info
        print("\n4. Testing S3 storage info...")
        info = s3_service.get_storage_info()
        print(f"   Storage info: {info}")
        
        # Test 5: Delete file
        print("\n5. Testing S3 file deletion...")
        delete_result = s3_service.delete_file(test_key)
        if delete_result['success']:
            print("✅ S3 file deletion successful")
        else:
            print(f"❌ S3 file deletion failed: {delete_result['error']}")
    
    except Exception as e:
        print(f"❌ S3 storage test failed: {str(e)}")
        import traceback
        traceback.print_exc()


def test_current_configuration():
    """Test the current storage configuration."""
    
    print("\n\n⚙️  Testing Current Configuration")
    print("=" * 50)
    
    print(f"Current storage type: {settings.STORAGE_TYPE}")
    print(f"Local storage path: {settings.LOCAL_STORAGE_PATH}")
    print(f"Local storage URL prefix: {settings.LOCAL_STORAGE_URL_PREFIX}")
    print(f"S3 bucket: {settings.S3_BUCKET_NAME}")
    print(f"S3 region: {settings.S3_REGION}")
    
    # Test current configuration
    try:
        current_service = StorageFactory.get_storage_service()
        print(f"\n✅ Current storage service: {type(current_service).__name__}")
        
        # Test basic functionality
        test_content = b"Configuration test file"
        test_key = "cvs/config_test.txt"
        
        upload_result = current_service.upload_file(
            file_bytes=test_content,
            key=test_key,
            content_type="text/plain"
        )
        
        if upload_result['success']:
            print(f"✅ Upload test successful: {upload_result['url']}")
            
            # Clean up
            current_service.delete_file(test_key)
            print("✅ Cleanup successful")
        else:
            print(f"❌ Upload test failed: {upload_result['error']}")
    
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")


def main():
    """Run all storage tests."""
    
    print("🧪 Storage Abstraction Layer Tests")
    print("=" * 60)
    
    test_storage_factory()
    test_local_storage()
    test_s3_storage()
    test_current_configuration()
    
    print("\n" + "=" * 60)
    print("🎉 Storage abstraction tests completed!")
    print("\nTo switch storage types, update STORAGE_TYPE in your .env file:")
    print("  STORAGE_TYPE=local  # for local file system")
    print("  STORAGE_TYPE=s3     # for S3 storage")


if __name__ == "__main__":
    main()
