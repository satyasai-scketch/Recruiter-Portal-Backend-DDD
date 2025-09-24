from sqlalchemy import Column, String, ForeignKey, Integer, UniqueConstraint, CheckConstraint, Enum
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from app.db.base import Base

LEVEL_ENUM = Enum("L1", "L2", "L3", "L4", "L5", name="level_enum", native_enum=False)


class PersonaModel(Base):
	__tablename__ = "personas"

	id = Column(String, primary_key=True)
	job_description_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
	name = Column(String, nullable=False)
	# Deprecated: prefer hierarchical categories
	weights = Column(JSON, nullable=True)
	# Deprecated: prefer hierarchical categories
	intervals = Column(JSON, nullable=True, default=dict)

	# Relationships
	job_description = relationship("JobDescriptionModel", back_populates="personas")
	categories = relationship("PersonaCategoryModel", back_populates="persona", cascade="all, delete-orphan")


class PersonaCategoryModel(Base):
	__tablename__ = "persona_categories"
	__table_args__ = (
		UniqueConstraint("persona_id", "name", name="uq_persona_category_name"),
		CheckConstraint("weight_percentage BETWEEN 0 AND 100", name="ck_weight_pct_range"),
	)

	id = Column(String, primary_key=True)
	persona_id = Column(String, ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
	name = Column(String, nullable=False)
	weight_percentage = Column(Integer, nullable=False)

	# Relationships
	persona = relationship("PersonaModel", back_populates="categories")
	subcategories = relationship("PersonaSubcategoryModel", back_populates="category", cascade="all, delete-orphan")


class PersonaSubcategoryModel(Base):
	__tablename__ = "persona_subcategories"
	__table_args__ = (
		UniqueConstraint("category_id", "name", name="uq_persona_subcategory_name"),
		CheckConstraint("weight_percentage BETWEEN 0 AND 100", name="ck_weight_pct_range"),
	)

	id = Column(String, primary_key=True)
	category_id = Column(String, ForeignKey("persona_categories.id", ondelete="CASCADE"), nullable=False, index=True)
	name = Column(String, nullable=False)
	weight_percentage = Column(Integer, nullable=False)
	level = Column(LEVEL_ENUM, nullable=True)

	# Relationships
	category = relationship("PersonaCategoryModel", back_populates="subcategories")
