#!/usr/bin/env python3
"""
Setup Default Roles Script

This script creates default user roles in the database.
"""

import sys
from pathlib import Path
from uuid import uuid4

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.db.session import SessionLocal
from app.repositories.role_repo import RoleRepository

def setup_default_roles():
    """Create default roles in the database."""
    print("🔧 Setting up default user roles...")
    
    db = SessionLocal()
    role_repo = RoleRepository()
    
    default_roles = [
        {"name": "Recruiter"},
        {"name": "Hiring Manager"},
        {"name": "Admin"},
    ]
    
    created_roles = []
    
    try:
        for role_data in default_roles:
            # Check if role already exists
            existing_role = role_repo.get_by_name(db, role_data["name"])
            if existing_role:
                print(f"   ✅ Role '{role_data['name']}' already exists (ID: {existing_role.id})")
                created_roles.append(existing_role)
            else:
                # Create new role
                role_dict = {"id": str(uuid4()), "name": role_data["name"]}
                new_role = role_repo.create(db, role_dict)
                print(f"   ✅ Created role '{new_role.name}' (ID: {new_role.id})")
                created_roles.append(new_role)
        
        print(f"\n🎯 Successfully set up {len(created_roles)} default roles!")
        print("\n📋 Available Roles:")
        for role in created_roles:
            print(f"   - {role.name} (ID: {role.id})")
        
        print("\n💡 You can now use these role IDs in user signup:")
        print("   Example: role_id: 'role-uuid-here'")
        
    except Exception as e:
        print(f"❌ Error setting up roles: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_default_roles()
