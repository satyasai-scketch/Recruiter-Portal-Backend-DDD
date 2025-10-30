"""
Persona Change Tracking Service

This service handles comprehensive change tracking for persona updates,
comparing old and new values and creating detailed audit logs.
"""

from typing import Dict, List, Any, Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models.persona import (
    PersonaModel, PersonaCategoryModel, PersonaSubcategoryModel,
    PersonaSkillsetModel, PersonaNotesModel, PersonaChangeLogModel
)


class PersonaChangeTracker:
    """Service for tracking and logging persona changes."""
    
    def __init__(self):
        self.change_logs: List[PersonaChangeLogModel] = []
    
    def track_persona_changes(
        self, 
        db: Session, 
        persona_id: str, 
        old_persona: PersonaModel, 
        new_data: Dict[str, Any], 
        changed_by: str
    ) -> List[PersonaChangeLogModel]:
        """
        Track all changes made to a persona and its nested entities.
        
        Args:
            db: Database session
            persona_id: ID of the persona being updated
            old_persona: The current persona model from database
            new_data: The new data being applied
            changed_by: User ID making the changes
            
        Returns:
            List of change log entries
        """
        self.change_logs = []
        
        # Track persona-level changes
        self._track_persona_fields(old_persona, new_data, changed_by)
        
        # Track category changes (includes notes and subcategories with skillsets)
        self._track_category_changes(persona_id, old_persona, new_data, changed_by)
        
        return self.change_logs
    
    def _track_persona_fields(
        self, 
        old_persona: PersonaModel, 
        new_data: Dict[str, Any], 
        changed_by: str
    ) -> None:
        """Track changes to persona-level fields."""
        fields_to_track = ['name', 'role_name', 'role_id', 'persona_notes']
        
        for field in fields_to_track:
            if field in new_data:
                old_value = getattr(old_persona, field, None)
                new_value = new_data[field]
                
                if old_value != new_value:
                    self._add_change_log(
                        persona_id=old_persona.id,
                        entity_type="persona",
                        entity_id=old_persona.id,
                        field_name=field,
                        old_value=str(old_value) if old_value is not None else None,
                        new_value=str(new_value) if new_value is not None else None,
                        changed_by=changed_by
                    )
    
    def _track_category_changes(
        self, 
        persona_id: str, 
        old_persona: PersonaModel, 
        new_data: Dict[str, Any], 
        changed_by: str
    ) -> None:
        """Track changes to categories and subcategories."""
        if 'categories' not in new_data:
            return
            
        new_categories = new_data['categories']
        old_categories = {cat.id: cat for cat in old_persona.categories}
        
        # Track category modifications and additions
        for new_cat in new_categories:
            cat_id = new_cat.get('id')
            
            if cat_id and cat_id in old_categories:
                # Existing category - track field changes
                old_cat = old_categories[cat_id]
                self._track_category_fields(old_cat, new_cat, changed_by)
                
                # Track category notes changes
                if 'notes' in new_cat:
                    self._track_category_notes_changes(old_cat, new_cat['notes'], changed_by)
                
                # Track subcategory changes
                if 'subcategories' in new_cat:
                    self._track_subcategory_changes(old_cat, new_cat, changed_by)
            else:
                # New category - track as addition
                new_cat_id = cat_id or str(uuid4())
                self._add_change_log(
                    persona_id=persona_id,
                    entity_type="category",
                    entity_id=new_cat_id,
                    field_name="category_added",
                    old_value=None,
                    new_value=new_cat.get('name', ''),
                    changed_by=changed_by
                )
                
                # Track all fields of new category
                self._track_new_category_fields(persona_id, new_cat_id, new_cat, changed_by)
                
                # Track new category notes
                if 'notes' in new_cat:
                    self._track_new_category_notes(persona_id, new_cat_id, new_cat['notes'], changed_by)
                
                # Track new subcategories
                if 'subcategories' in new_cat:
                    self._track_new_subcategories(persona_id, new_cat_id, new_cat, changed_by)
        
        # Track category deletions
        new_cat_ids = {cat.get('id') for cat in new_categories if cat.get('id')}
        for old_cat_id, old_cat in old_categories.items():
            if old_cat_id not in new_cat_ids:
                self._add_change_log(
                    persona_id=persona_id,
                    entity_type="category",
                    entity_id=old_cat_id,
                    field_name="category_deleted",
                    old_value=old_cat.name,
                    new_value=None,
                    changed_by=changed_by
                )
    
    def _track_category_fields(
        self, 
        old_cat: PersonaCategoryModel, 
        new_cat: Dict[str, Any], 
        changed_by: str
    ) -> None:
        """Track changes to category fields."""
        fields_to_track = ['name', 'weight_percentage', 'range_min', 'range_max', 'position']
        
        for field in fields_to_track:
            if field in new_cat:
                old_value = getattr(old_cat, field, None)
                new_value = new_cat[field]
                
                if old_value != new_value:
                    self._add_change_log(
                        persona_id=old_cat.persona_id,
                        entity_type="category",
                        entity_id=old_cat.id,
                        field_name=field,
                        old_value=str(old_value) if old_value is not None else None,
                        new_value=str(new_value) if new_value is not None else None,
                        changed_by=changed_by
                    )
    
    def _track_new_category_fields(
        self, 
        persona_id: str, 
        category_id: str, 
        new_cat: Dict[str, Any], 
        changed_by: str
    ) -> None:
        """Track all fields of a newly added category."""
        fields_to_track = ['name', 'weight_percentage', 'range_min', 'range_max', 'position']
        
        for field in fields_to_track:
            if field in new_cat:
                self._add_change_log(
                    persona_id=persona_id,
                    entity_type="category",
                    entity_id=category_id,
                    field_name=field,
                    old_value=None,
                    new_value=str(new_cat[field]) if new_cat[field] is not None else None,
                    changed_by=changed_by
                )
    
    def _track_category_notes_changes(
        self, 
        old_cat: PersonaCategoryModel, 
        new_notes: Any, 
        changed_by: str
    ) -> None:
        """Track changes to category notes."""
        # Get existing note for this category (single note, not a list)
        existing_note = old_cat.notes if old_cat.notes else None
        existing_note_id = existing_note.id if existing_note else None
        
        # Handle the note data (can be a single note object or a list)
        if new_notes:
            # If it's a list, take the first note; if it's a dict, use it directly
            if isinstance(new_notes, list):
                new_note = new_notes[0] if new_notes else None
            else:
                new_note = new_notes
            
            if new_note:
                note_id = new_note.get('id')
                
                if note_id and existing_note and note_id == existing_note_id:
                    # Existing note - track field changes
                    self._track_notes_fields(existing_note, new_note, changed_by)
                else:
                    # New note - track as addition
                    new_note_id = note_id or str(uuid4())
                    self._add_change_log(
                        persona_id=old_cat.persona_id,
                        entity_type="notes",
                        entity_id=new_note_id,
                        field_name="notes_added",
                        old_value=None,
                        new_value=new_note.get('custom_notes', ''),
                        changed_by=changed_by
                    )
        else:
            # No new notes - track deletion if there was an existing note
            if existing_note:
                self._add_change_log(
                    persona_id=old_cat.persona_id,
                    entity_type="notes",
                    entity_id=existing_note.id,
                    field_name="notes_deleted",
                    old_value=existing_note.custom_notes,
                    new_value=None,
                    changed_by=changed_by
                )
    
    def _track_new_category_notes(
        self, 
        persona_id: str, 
        category_id: str, 
        new_notes: Any, 
        changed_by: str
    ) -> None:
        """Track new notes for a category."""
        # Handle the note data (can be a single note object or a list)
        if new_notes:
            # If it's a list, take the first note; if it's a dict, use it directly
            if isinstance(new_notes, list):
                new_note = new_notes[0] if new_notes else None
            else:
                new_note = new_notes
            
            if new_note:
                new_note_id = str(uuid4())
                self._add_change_log(
                    persona_id=persona_id,
                    entity_type="notes",
                    entity_id=new_note_id,
                    field_name="notes_added",
                    old_value=None,
                    new_value=new_note.get('custom_notes', ''),
                    changed_by=changed_by
                )
    
    def _track_notes_fields(
        self, 
        old_note: PersonaNotesModel, 
        new_note: Dict[str, Any], 
        changed_by: str
    ) -> None:
        """Track changes to notes fields."""
        if 'custom_notes' in new_note:
            old_value = old_note.custom_notes
            new_value = new_note['custom_notes']
            
            if old_value != new_value:
                self._add_change_log(
                    persona_id=old_note.persona_id,
                    entity_type="notes",
                    entity_id=old_note.id,
                    field_name="custom_notes",
                    old_value=old_value,
                    new_value=new_value,
                    changed_by=changed_by
                )
    
    def _track_subcategory_changes(
        self, 
        old_cat: PersonaCategoryModel, 
        new_cat: Dict[str, Any], 
        changed_by: str
    ) -> None:
        """Track changes to subcategories within a category."""
        if 'subcategories' not in new_cat:
            return
            
        new_subcats = new_cat['subcategories']
        old_subcats = {sub.id: sub for sub in old_cat.subcategories}
        
        # Track subcategory modifications and additions
        for new_sub in new_subcats:
            sub_id = new_sub.get('id')
            
            if sub_id and sub_id in old_subcats:
                # Existing subcategory - track field changes
                old_sub = old_subcats[sub_id]
                self._track_subcategory_fields(old_sub, new_sub, changed_by)
                
                # Track subcategory skillset changes
                if 'skillset' in new_sub:
                    self._track_subcategory_skillset_changes(old_sub, new_sub['skillset'], changed_by)
            else:
                # New subcategory - track as addition
                new_sub_id = sub_id or str(uuid4())
                self._add_change_log(
                    persona_id=old_cat.persona_id,
                    entity_type="subcategory",
                    entity_id=new_sub_id,
                    field_name="subcategory_added",
                    old_value=None,
                    new_value=new_sub.get('name', ''),
                    changed_by=changed_by
                )
                
                # Track all fields of new subcategory
                self._track_new_subcategory_fields(old_cat.persona_id, new_sub_id, new_sub, changed_by)
                
                # Track new subcategory skillset
                if 'skillset' in new_sub:
                    self._track_new_subcategory_skillset(old_cat.persona_id, new_sub_id, new_sub['skillset'], changed_by)
        
        # Track subcategory deletions
        new_sub_ids = {sub.get('id') for sub in new_subcats if sub.get('id')}
        for old_sub_id, old_sub in old_subcats.items():
            if old_sub_id not in new_sub_ids:
                self._add_change_log(
                    persona_id=old_cat.persona_id,
                    entity_type="subcategory",
                    entity_id=old_sub_id,
                    field_name="subcategory_deleted",
                    old_value=old_sub.name,
                    new_value=None,
                    changed_by=changed_by
                )
    
    def _track_subcategory_fields(
        self, 
        old_sub: PersonaSubcategoryModel, 
        new_sub: Dict[str, Any], 
        changed_by: str
    ) -> None:
        """Track changes to subcategory fields."""
        fields_to_track = ['name', 'weight_percentage', 'range_min', 'range_max', 'level_id', 'position']
        
        for field in fields_to_track:
            if field in new_sub:
                old_value = getattr(old_sub, field, None)
                new_value = new_sub[field]
                
                if old_value != new_value:
                    self._add_change_log(
                        persona_id=old_sub.category.persona_id,
                        entity_type="subcategory",
                        entity_id=old_sub.id,
                        field_name=field,
                        old_value=str(old_value) if old_value is not None else None,
                        new_value=str(new_value) if new_value is not None else None,
                        changed_by=changed_by
                    )
    
    def _track_new_subcategory_fields(
        self, 
        persona_id: str, 
        subcategory_id: str, 
        new_sub: Dict[str, Any], 
        changed_by: str
    ) -> None:
        """Track all fields of a newly added subcategory."""
        fields_to_track = ['name', 'weight_percentage', 'range_min', 'range_max', 'level_id', 'position']
        
        for field in fields_to_track:
            if field in new_sub:
                self._add_change_log(
                    persona_id=persona_id,
                    entity_type="subcategory",
                    entity_id=subcategory_id,
                    field_name=field,
                    old_value=None,
                    new_value=str(new_sub[field]) if new_sub[field] is not None else None,
                    changed_by=changed_by
                )
    
    def _track_subcategory_skillset_changes(
        self, 
        old_sub: PersonaSubcategoryModel, 
        new_skillset: Any, 
        changed_by: str
    ) -> None:
        """Track changes to subcategory skillset."""
        # Find existing skillset for this subcategory
        old_skillset = None
        for skillset in old_sub.category.persona.skillsets:
            if skillset.persona_subcategory_id == old_sub.id:
                old_skillset = skillset
                break
        
        if new_skillset:
            if old_skillset:
                # Update existing skillset
                old_value = old_skillset.technologies
                new_value = new_skillset.get('technologies', [])
                
                if old_value != new_value:
                    self._add_change_log(
                        persona_id=old_sub.category.persona_id,
                        entity_type="skillset",
                        entity_id=old_skillset.id,
                        field_name="technologies",
                        old_value=str(old_value) if old_value is not None else None,
                        new_value=str(new_value) if new_value is not None else None,
                        changed_by=changed_by
                    )
            else:
                # New skillset
                new_skillset_id = str(uuid4())
                self._add_change_log(
                    persona_id=old_sub.category.persona_id,
                    entity_type="skillset",
                    entity_id=new_skillset_id,
                    field_name="skillset_added",
                    old_value=None,
                    new_value=str(new_skillset.get('technologies', [])),
                    changed_by=changed_by
                )
        else:
            # No new skillset - track deletion if there was an existing skillset
            if old_skillset:
                self._add_change_log(
                    persona_id=old_sub.category.persona_id,
                    entity_type="skillset",
                    entity_id=old_skillset.id,
                    field_name="skillset_deleted",
                    old_value=str(old_skillset.technologies) if old_skillset.technologies is not None else None,
                    new_value=None,
                    changed_by=changed_by
                )
    
    def _track_new_subcategory_skillset(
        self, 
        persona_id: str, 
        subcategory_id: str, 
        new_skillset: Any, 
        changed_by: str
    ) -> None:
        """Track new skillset for a subcategory."""
        if new_skillset:
            new_skillset_id = str(uuid4())
            self._add_change_log(
                persona_id=persona_id,
                entity_type="skillset",
                entity_id=new_skillset_id,
                field_name="skillset_added",
                old_value=None,
                new_value=str(new_skillset.get('technologies', [])),
                changed_by=changed_by
            )
    
    def _track_new_subcategories(
        self, 
        persona_id: str, 
        category_id: str, 
        new_cat: Dict[str, Any], 
        changed_by: str
    ) -> None:
        """Track all subcategories of a newly added category."""
        if 'subcategories' not in new_cat:
            return
            
        for new_sub in new_cat['subcategories']:
            new_sub_id = new_sub.get('id') or str(uuid4())
            self._add_change_log(
                persona_id=persona_id,
                entity_type="subcategory",
                entity_id=new_sub_id,
                field_name="subcategory_added",
                old_value=None,
                new_value=new_sub.get('name', ''),
                changed_by=changed_by
            )
            self._track_new_subcategory_fields(persona_id, new_sub_id, new_sub, changed_by)
            
            # Track new subcategory skillset
            if 'skillset' in new_sub:
                self._track_new_subcategory_skillset(persona_id, new_sub_id, new_sub['skillset'], changed_by)
    
    def _add_change_log(
        self, 
        persona_id: str, 
        entity_type: str, 
        entity_id: str, 
        field_name: str, 
        old_value: Optional[str], 
        new_value: Optional[str], 
        changed_by: str
    ) -> None:
        """Add a change log entry."""
        change_log = PersonaChangeLogModel(
            id=str(uuid4()),
            persona_id=persona_id,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by
        )
        self.change_logs.append(change_log)
