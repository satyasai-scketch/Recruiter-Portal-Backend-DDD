from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
import asyncio
import concurrent.futures

from app.repositories.persona_warning_repo import SQLAlchemyPersonaWarningRepository
from app.db.models.persona import PersonaWeightWarningModel
from app.core.config import settings


class PersonaWarningService:
    """Service for managing persona weight warnings"""
    
    def __init__(self):
        self.warning_repo = SQLAlchemyPersonaWarningRepository()
    
    async def generate_warnings(
        self, 
        db: Session, 
        persona_data: Dict
    ) -> Dict[str, Any]:
        """
        Generate all warning messages for a persona structure.
        
        Args:
            db: Database session
            persona_data: Full persona structure (PersonaCreate format)
        
        Returns:
            Dict with temp persona_id and all generated warnings
        """
        # Import here to avoid circular dependency
        from app.services.persona_generation import OpenAIPersonaGenerator
        
        # Initialize generator
        persona_generator = OpenAIPersonaGenerator(
            api_key=settings.OPENAI_API_KEY,
            model=getattr(settings, "PERSONA_GENERATION_MODEL", "gpt-4o")
        )
        
        # Generate temporary persona ID for preview
        temp_persona_id = f"preview-{str(uuid4())[:8]}"
        
        # Run async warning generation using LLM
        warnings_data = await persona_generator.warning_generator.generate_all_warnings(
            persona_data=persona_data,
            jd_analysis=None  # Not needed - persona structure has all info
        )
        
        # Store warnings in database
        warning_models = []
        for warning in warnings_data.get('warnings', []):
            warning_model = PersonaWeightWarningModel(
                id=str(uuid4()),
                persona_id=temp_persona_id,
                entity_type=warning['entity_type'],
                entity_name=warning['entity_name'],
                below_min_message=warning['below_min_message'],
                above_max_message=warning['above_max_message']
            )
            warning_models.append(warning_model)
        
        # Bulk create
        created_warnings = self.warning_repo.bulk_create(db, warning_models)
        
        return {
            'persona_id': temp_persona_id,
            'total_warnings': len(created_warnings),
            'warnings': [
                {
                    'entity_type': w.entity_type,
                    'entity_name': w.entity_name,
                    'below_min_message': w.below_min_message,
                    'above_max_message': w.above_max_message
                }
                for w in created_warnings
            ],
            'generated_at': created_warnings[0].generated_at if created_warnings else None
        }
    
    def generate_warnings_sync(self, db: Session, persona_data: Dict) -> Dict[str, Any]:
        """Synchronous wrapper for generate_warnings"""
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.generate_warnings(db, persona_data)
                )
                return future.result()
        except RuntimeError:
            return asyncio.run(self.generate_warnings(db, persona_data))
    
    def get_warning(
        self, 
        db: Session, 
        persona_id: str, 
        entity_type: str, 
        entity_name: str, 
        violation_type: str
    ) -> Dict[str, Any]:
        """
        Get specific warning message for a violated entity.
        
        Args:
            db: Database session
            persona_id: Persona ID (or preview-xxx for unsaved)
            entity_type: "category" or "subcategory"
            entity_name: Name of the entity
            violation_type: "below_min" or "above_max"
        
        Returns:
            Dict with the warning message
        """
        warning = self.warning_repo.get_by_entity(
            db=db,
            persona_id=persona_id,
            entity_type=entity_type,
            entity_name=entity_name
        )
        
        if not warning:
            raise ValueError(f"Warning not found for {entity_type} '{entity_name}' in persona {persona_id}")
        
        message = warning.below_min_message if violation_type == "below_min" else warning.above_max_message
        
        return {
            'entity_type': warning.entity_type,
            'entity_name': warning.entity_name,
            'violation_type': violation_type,
            'message': message
        }
    async def generate_single_entity_warning(
        self,
        db: Session,
        persona_id: str,
        entity_type: str,
        entity_name: str,
        entity_data: Dict
    ) -> Dict[str, Any]:
        """
        Generate warning for a SINGLE entity only (lazy generation).
        
        Args:
            persona_id: Persona ID
            entity_type: "category" or "subcategory"
            entity_name: Name of violated entity
            entity_data: Just the entity info {name, weight, range_min, range_max, technologies, parent_category}
        """
        # Check if already exists
        existing = self.warning_repo.get_by_entity(
            db=db,
            persona_id=persona_id,
            entity_type=entity_type,
            entity_name=entity_name
        )
        
        if existing:
            print(f"✅ Warning already exists for {entity_type} '{entity_name}'")
            return {
                'entity_type': existing.entity_type,
                'entity_name': existing.entity_name,
                'below_min_message': existing.below_min_message,
                'above_max_message': existing.above_max_message,
                'already_existed': True
            }
        
        # Generate new
        from app.services.persona_generation import OpenAIPersonaGenerator
        
        persona_generator = OpenAIPersonaGenerator(
            api_key=settings.OPENAI_API_KEY,
            model=getattr(settings, "PERSONA_GENERATION_MODEL", "gpt-4o")
        )
        
        warning_data = await persona_generator.warning_generator.generate_single_warning(
            entity_type=entity_type,
            entity_data=entity_data
        )
        
        warning_model = PersonaWeightWarningModel(
            id=str(uuid4()),
            persona_id=persona_id,
            entity_type=entity_type,
            entity_name=entity_name,
            below_min_message=warning_data['below_min_message'],
            above_max_message=warning_data['above_max_message']
        )
        
        created = self.warning_repo.create(db, warning_model)
        
        print(f"✅ Generated new warning for {entity_type} '{entity_name}'")
        
        return {
            'entity_type': created.entity_type,
            'entity_name': created.entity_name,
            'below_min_message': created.below_min_message,
            'above_max_message': created.above_max_message,
            'already_existed': False
        }
    
    def generate_single_entity_warning_sync(
        self,
        db: Session,
        persona_id: str,
        entity_type: str,
        entity_name: str,
        entity_data: Dict
    ) -> Dict[str, Any]:
        """Sync wrapper for single entity generation"""
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.generate_single_entity_warning(
                        db, persona_id, entity_type, entity_name, entity_data
                    )
                )
                return future.result()
        except RuntimeError:
            return asyncio.run(
                self.generate_single_entity_warning(
                    db, persona_id, entity_type, entity_name, entity_data
                )
            )
    
    def get_or_generate_warning(
        self,
        db: Session,
        persona_id: Optional[str],
        entity_type: str,
        entity_name: str,
        violation_type: str,
        entity_data: Optional[Dict] = None  # ✅ NOW OPTIONAL
    ) -> Dict[str, Any]:
        """
        Smart method: Get warning or generate on-the-fly.
        """
        # Generate persona_id if not provided (first call)
        if not persona_id:
            persona_id = f"preview-{str(uuid4())[:8]}"
            print(f"🆕 Generated new persona ID: {persona_id}")
        
        # Try to fetch existing warning
        warning = self.warning_repo.get_by_entity(
            db=db,
            persona_id=persona_id,
            entity_type=entity_type,
            entity_name=entity_name
        )
        
        # If exists, return it (FAST PATH - no entity_data needed)
        if warning:
            message = warning.below_min_message if violation_type == "below_min" else warning.above_max_message
            print(f"✅ Found existing warning for {entity_type} '{entity_name}'")
            return {
                'persona_id': persona_id,
                'entity_type': warning.entity_type,
                'entity_name': warning.entity_name,
                'violation_type': violation_type,
                'message': message,
                'generated_now': False
            }
        
        # ✅ NEW: Validate entity_data is provided when generating
        if not entity_data:
            raise ValueError(
                f"entity_data is required when generating warning for {entity_type} '{entity_name}'. "
                f"This warning does not exist yet for persona '{persona_id}'."
            )
        
        # Generate on-the-fly (SLOW PATH - first time only)
        print(f"⚡ Generating warning for {entity_type} '{entity_name}'")
        generated = self.generate_single_entity_warning_sync(
            db, persona_id, entity_type, entity_name, entity_data
        )
        
        message = generated['below_min_message'] if violation_type == "below_min" else generated['above_max_message']
        
        return {
            'persona_id': persona_id,
            'entity_type': generated['entity_type'],
            'entity_name': generated['entity_name'],
            'violation_type': violation_type,
            'message': message,
            'generated_now': True
        }

    def list_warnings(self, db: Session, persona_id: str) -> List[PersonaWeightWarningModel]:
        """List all warnings for a persona"""
        return self.warning_repo.list_by_persona(db, persona_id)
    
    def link_warnings_to_persona(
        self, 
        db: Session, 
        temp_persona_id: str, 
        saved_persona_id: str
    ) -> Dict[str, Any]:
        """
        Link preview warnings to saved persona.
        
        Args:
            db: Database session
            temp_persona_id: Temporary preview ID (e.g., "preview-a1b2c3d4")
            saved_persona_id: Real persona ID after save
        
        Returns:
            Dict with link result
        """
        updated_count = self.warning_repo.update_persona_id(
            db=db,
            old_persona_id=temp_persona_id,
            new_persona_id=saved_persona_id
        )
        
        return {
            'temp_persona_id': temp_persona_id,
            'saved_persona_id': saved_persona_id,
            'warnings_linked': updated_count
        }