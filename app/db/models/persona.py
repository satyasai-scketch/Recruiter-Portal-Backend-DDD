from sqlalchemy import Column, String, ForeignKey, Integer, UniqueConstraint, CheckConstraint, Enum, DateTime, Text, Float, Index
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# LEVEL_ENUM = Enum("L1", "L2", "L3", "L4", "L5", name="level_enum", native_enum=False)


class PersonaModel(Base):
	__tablename__ = "personas"

	id = Column(String, primary_key=True)
	job_description_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
	name = Column(String, nullable=False)
	role_name = Column(String, nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
	# Deprecated: prefer hierarchical categories
	weights = Column(JSON, nullable=True)
	# Deprecated: prefer hierarchical categories
	intervals = Column(JSON, nullable=True, default=dict)

	# Relationships
	job_description = relationship("JobDescriptionModel", back_populates="personas")
	categories = relationship("PersonaCategoryModel", back_populates="persona", cascade="all, delete-orphan")
	skillsets = relationship("PersonaSkillsetModel", back_populates="persona", cascade="all, delete-orphan")
	notes = relationship("PersonaNotesModel", back_populates="persona", cascade="all, delete-orphan")
	change_logs = relationship("PersonaChangeLogModel", back_populates="persona", cascade="all, delete-orphan")
	creator = relationship("UserModel", foreign_keys=[created_by])

class PersonaCategoryModel(Base):
	__tablename__ = "persona_categories"
	__table_args__ = (
		UniqueConstraint("persona_id", "name", name="uq_persona_category_name"),
		CheckConstraint("weight_percentage BETWEEN 0 AND 100", name="ck_weight_pct_range"),
		CheckConstraint("range_min <= range_max", name="ck_range_min_max"),
	)

	id = Column(String, primary_key=True)
	persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
	name = Column(String, nullable=False)
	weight_percentage = Column(Integer, nullable=False)
	range_min = Column(Float, nullable=True)
	range_max = Column(Float, nullable=True)
	position = Column(Integer, nullable=True)
	notes_id = Column(String, ForeignKey("persona_notes.id", ondelete="SET NULL"), nullable=True)

	# Relationships
	persona = relationship("PersonaModel", back_populates="categories")
	subcategories = relationship("PersonaSubcategoryModel", back_populates="category", cascade="all, delete-orphan")
	notes = relationship("PersonaNotesModel", foreign_keys=[notes_id])
	skillsets = relationship("PersonaSkillsetModel", back_populates="category", foreign_keys="PersonaSkillsetModel.persona_category_id", cascade="all, delete-orphan")


class PersonaSubcategoryModel(Base):
	__tablename__ = "persona_subcategories"
	__table_args__ = (
		UniqueConstraint("category_id", "name", name="uq_persona_subcategory_name"),
		CheckConstraint("weight_percentage BETWEEN 0 AND 100", name="ck_weight_pct_range"),
		CheckConstraint("range_min <= range_max", name="ck_range_min_max"),
	)

	id = Column(String, primary_key=True)
	category_id = Column(String, ForeignKey("persona_categories.id", ondelete="CASCADE"), nullable=False, index=True)
	name = Column(String, nullable=False)
	weight_percentage = Column(Integer, nullable=False)
	range_min = Column(Float, nullable=True)
	range_max = Column(Float, nullable=True)
	level_id = Column(String, ForeignKey("persona_levels.id", ondelete="SET NULL"), nullable=True)
	skillset_id = Column(String, ForeignKey("persona_skillsets.id", ondelete="SET NULL"), nullable=True)
	position = Column(Integer, nullable=True)

	# Relationships
	category = relationship("PersonaCategoryModel", back_populates="subcategories")
	level = relationship("PersonaLevelModel", foreign_keys=[level_id])
	skillset = relationship("PersonaSkillsetModel", foreign_keys=[skillset_id])


class PersonaLevelModel(Base):
	__tablename__ = "persona_levels"

	id = Column(String, primary_key=True)
	name = Column(String, nullable=False)
	position = Column(Integer, nullable=True)

	# Relationships
	subcategories = relationship("PersonaSubcategoryModel", back_populates="level")


class PersonaSkillsetModel(Base):
	__tablename__ = "persona_skillsets"

	id = Column(String, primary_key=True)
	persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
	persona_category_id = Column(String, ForeignKey("persona_categories.id", ondelete="CASCADE"), nullable=True, index=True)
	persona_subcategory_id = Column(String, ForeignKey("persona_subcategories.id", ondelete="CASCADE"), nullable=True, index=True)
	technologies = Column(JSON, nullable=True)

	# Relationships
	persona = relationship("PersonaModel", back_populates="skillsets")
	category = relationship("PersonaCategoryModel", back_populates="skillsets", foreign_keys=[persona_category_id])
	subcategory = relationship("PersonaSubcategoryModel", foreign_keys=[persona_subcategory_id])


class PersonaNotesModel(Base):
	__tablename__ = "persona_notes"

	id = Column(String, primary_key=True)
	persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
	category_id = Column(String, ForeignKey("persona_categories.id", ondelete="CASCADE"), nullable=True, index=True)
	custom_notes = Column(Text, nullable=True)

	# Relationships
	persona = relationship("PersonaModel", back_populates="notes")
	category = relationship("PersonaCategoryModel", foreign_keys=[category_id])


class PersonaChangeLogModel(Base):
	__tablename__ = "persona_change_logs"

	id = Column(String, primary_key=True)
	persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
	entity_type = Column(String, nullable=False)  # e.g. "persona", "category", "subcategory"
	entity_id = Column(String, nullable=False)  # which record changed
	field_name = Column(String, nullable=False)  # e.g. "weight_percentage", "name", "level"
	old_value = Column(Text, nullable=True)  # previous value (stored as string)
	new_value = Column(Text, nullable=True)  # new value (stored as string)
	changed_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
	changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

	# Relationships
	persona = relationship("PersonaModel", back_populates="change_logs")
	user = relationship("UserModel", foreign_keys=[changed_by])


class PersonaWeightWarningModel(Base):
    __tablename__ = "persona_weight_warnings"
    # Primary key
    id = Column(String, primary_key=True)
    # Link to actual persona (nullable because generated before save)
    persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=True, index=True)
    # Which entity this warning is for
    entity_type = Column(String, nullable=False)  # "category" | "subcategory"
    entity_name = Column(String, nullable=False, index=True)  # "Technical Skills"
    # The TWO warning messages
    below_min_message = Column(Text, nullable=False)
    above_max_message = Column(Text, nullable=False)
    # Metadata
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        # One warning per entity per persona
        UniqueConstraint("persona_id", "entity_type", "entity_name", name="uq_persona_warning"),
        Index("idx_entity_lookup", "persona_id", "entity_type", "entity_name"),
    )
    # Relationship
    persona = relationship("PersonaModel", backref="weight_warnings")
