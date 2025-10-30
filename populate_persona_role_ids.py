#!/usr/bin/env python3
"""
Script to populate role_id for existing personas that have null role_id values.

This script will:
1. Find all personas where role_id is null
2. Get the role_id from their associated job_description
3. Update the persona with the correct role_id
4. Provide a summary of the updates made
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.db.session import get_db
from app.db.models.persona import PersonaModel
from app.db.models.job_description import JobDescriptionModel
from app.db.models.job_role import JobRoleModel


def get_database_url():
    """Get database URL from environment or use default SQLite."""
    import os
    from app.core.config import settings
    
    # Try to get from settings first
    try:
        return settings.DATABASE_URL
    except:
        # Fallback to SQLite
        return "sqlite:///./app.db"


def populate_persona_role_ids():
    """Populate role_id for personas that have null role_id values."""
    
    # Create database connection
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        print("🔍 Finding personas with null role_id...")
        
        # Query to find personas with null role_id and get their job description's role_id
        query = text("""
            SELECT 
                p.id as persona_id,
                p.name as persona_name,
                p.job_description_id,
                jd.role_id as job_description_role_id,
                jr.name as role_name
            FROM personas p
            JOIN job_descriptions jd ON p.job_description_id = jd.id
            LEFT JOIN job_roles jr ON jd.role_id = jr.id
            WHERE p.role_id IS NULL
        """)
        
        result = db.execute(query)
        personas_to_update = result.fetchall()
        
        if not personas_to_update:
            print("✅ No personas found with null role_id. All personas already have role_id populated.")
            return
        
        print(f"📊 Found {len(personas_to_update)} personas with null role_id:")
        print("-" * 80)
        
        # Display personas that will be updated
        for persona in personas_to_update:
            print(f"Persona: {persona.persona_name} (ID: {persona.persona_id})")
            print(f"  Job Description ID: {persona.job_description_id}")
            print(f"  Role ID: {persona.job_description_role_id}")
            print(f"  Role Name: {persona.role_name}")
            print()
        
        # Confirm before proceeding
        response = input("Do you want to proceed with updating these personas? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled.")
            return
        
        print("\n🔄 Updating personas...")
        
        # Update each persona
        updated_count = 0
        failed_updates = []
        
        for persona in personas_to_update:
            try:
                # Update the persona with the role_id from job_description
                update_query = text("""
                    UPDATE personas 
                    SET role_id = :role_id 
                    WHERE id = :persona_id
                """)
                
                db.execute(update_query, {
                    'role_id': persona.job_description_role_id,
                    'persona_id': persona.persona_id
                })
                
                updated_count += 1
                print(f"✅ Updated persona '{persona.persona_name}' with role_id: {persona.job_description_role_id}")
                
            except Exception as e:
                error_msg = f"Failed to update persona '{persona.persona_name}': {str(e)}"
                print(f"❌ {error_msg}")
                failed_updates.append(error_msg)
        
        # Commit all changes
        db.commit()
        
        print("\n" + "=" * 80)
        print("📈 SUMMARY")
        print("=" * 80)
        print(f"✅ Successfully updated: {updated_count} personas")
        
        if failed_updates:
            print(f"❌ Failed updates: {len(failed_updates)}")
            for error in failed_updates:
                print(f"   - {error}")
        
        # Verify the updates
        print("\n🔍 Verifying updates...")
        verification_query = text("""
            SELECT COUNT(*) as count
            FROM personas 
            WHERE role_id IS NULL
        """)
        
        result = db.execute(verification_query)
        remaining_null_count = result.fetchone().count
        
        if remaining_null_count == 0:
            print("✅ All personas now have role_id populated!")
        else:
            print(f"⚠️  {remaining_null_count} personas still have null role_id")
        
        # Show final statistics
        total_personas_query = text("SELECT COUNT(*) as count FROM personas")
        result = db.execute(total_personas_query)
        total_personas = result.fetchone().count
        
        personas_with_role_id_query = text("SELECT COUNT(*) as count FROM personas WHERE role_id IS NOT NULL")
        result = db.execute(personas_with_role_id_query)
        personas_with_role_id = result.fetchone().count
        
        print(f"\n📊 Final Statistics:")
        print(f"   Total personas: {total_personas}")
        print(f"   Personas with role_id: {personas_with_role_id}")
        print(f"   Personas without role_id: {total_personas - personas_with_role_id}")
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {str(e)}")
        db.rollback()
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        db.rollback()
    finally:
        db.close()


def verify_persona_role_relationships():
    """Verify that all personas have valid role_id relationships."""
    
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        print("\n🔍 Verifying persona-role relationships...")
        
        # Check for personas with role_id that don't exist in job_roles
        invalid_role_query = text("""
            SELECT p.id, p.name, p.role_id
            FROM personas p
            LEFT JOIN job_roles jr ON p.role_id = jr.id
            WHERE p.role_id IS NOT NULL AND jr.id IS NULL
        """)
        
        result = db.execute(invalid_role_query)
        invalid_roles = result.fetchall()
        
        if invalid_roles:
            print(f"⚠️  Found {len(invalid_roles)} personas with invalid role_id:")
            for persona in invalid_roles:
                print(f"   - {persona.name} (ID: {persona.id}) has invalid role_id: {persona.role_id}")
        else:
            print("✅ All personas with role_id have valid role references")
        
        # Check for personas where role_id doesn't match job_description's role_id
        mismatch_query = text("""
            SELECT 
                p.id, 
                p.name, 
                p.role_id as persona_role_id,
                jd.role_id as jd_role_id
            FROM personas p
            JOIN job_descriptions jd ON p.job_description_id = jd.id
            WHERE p.role_id IS NOT NULL 
            AND p.role_id != jd.role_id
        """)
        
        result = db.execute(mismatch_query)
        mismatches = result.fetchall()
        
        if mismatches:
            print(f"⚠️  Found {len(mismatches)} personas where role_id doesn't match job_description's role_id:")
            for persona in mismatches:
                print(f"   - {persona.name} (ID: {persona.id})")
                print(f"     Persona role_id: {persona.persona_role_id}")
                print(f"     JD role_id: {persona.jd_role_id}")
        else:
            print("✅ All personas have role_id matching their job_description's role_id")
            
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Persona Role ID Population Script")
    print("=" * 50)
    
    try:
        # First, populate missing role_ids
        populate_persona_role_ids()
        
        # Then verify the relationships
        verify_persona_role_relationships()
        
        print("\n🎉 Script completed successfully!")
        
    except KeyboardInterrupt:
        print("\n❌ Script interrupted by user")
    except Exception as e:
        print(f"\n❌ Script failed with error: {str(e)}")
        sys.exit(1)
