# app/repositories/company_repo.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.db.models.company import CompanyModel

class CompanyRepository:
    """Repository for Company data access operations."""
    
    def create(self, db: Session, company_data: dict) -> CompanyModel:
        """Create a new company."""
        try:
            company = CompanyModel(**company_data)
            db.add(company)
            db.commit()
            db.refresh(company)
            return company
        except Exception as e:
            db.rollback()
            raise e
    
    def get_by_id(self, db: Session, company_id: str) -> Optional[CompanyModel]:
        """Get company by ID."""
        return db.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[CompanyModel]:
        """Get company by name (case-insensitive)."""
        return db.query(CompanyModel).filter(
            func.lower(CompanyModel.name) == name.lower().strip()
        ).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[CompanyModel]:
        """Get company by email address (case-insensitive)."""
        return db.query(CompanyModel).filter(
            func.lower(CompanyModel.email_address) == email.lower().strip()
        ).first()
    
    def get_by_website(self, db: Session, website_url: str) -> Optional[CompanyModel]:
        """Get company by website URL (case-insensitive)."""
        return db.query(CompanyModel).filter(
            func.lower(CompanyModel.website_url) == website_url.lower().strip()
        ).first()
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[CompanyModel]:
        """Get all companies with pagination."""
        return db.query(CompanyModel).offset(skip).limit(limit).all()
    
    def search(self, db: Session, search_criteria: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[CompanyModel]:
        """Search companies based on criteria."""
        query = db.query(CompanyModel)
        
        # Apply search filters
        if 'name_contains' in search_criteria:
            query = query.filter(
                func.lower(CompanyModel.name).contains(search_criteria['name_contains'])
            )
        
        if 'city_contains' in search_criteria:
            query = query.filter(
                func.lower(CompanyModel.city).contains(search_criteria['city_contains'])
            )
        
        if 'country_contains' in search_criteria:
            query = query.filter(
                func.lower(CompanyModel.country).contains(search_criteria['country_contains'])
            )
        
        # Apply pagination
        return query.offset(skip).limit(limit).all()
    
    def count(self, db: Session) -> int:
        """Count total number of companies."""
        return db.query(CompanyModel).count()
    
    def count_search(self, db: Session, search_criteria: Dict[str, Any]) -> int:
        """Count companies matching search criteria."""
        query = db.query(CompanyModel)
        
        # Apply search filters
        if 'name_contains' in search_criteria:
            query = query.filter(
                func.lower(CompanyModel.name).contains(search_criteria['name_contains'])
            )
        
        if 'city_contains' in search_criteria:
            query = query.filter(
                func.lower(CompanyModel.city).contains(search_criteria['city_contains'])
            )
        
        if 'country_contains' in search_criteria:
            query = query.filter(
                func.lower(CompanyModel.country).contains(search_criteria['country_contains'])
            )
        
        return query.count()
    
    def update(self, db: Session, company: CompanyModel) -> CompanyModel:
        """Update an existing company."""
        try:
            db.commit()
            db.refresh(company)
            return company
        except Exception as e:
            db.rollback()
            raise e
    
    def delete(self, db: Session, company_id: str) -> bool:
        """Delete a company by ID."""
        try:
            company = self.get_by_id(db, company_id)
            if company:
                db.delete(company)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            raise e
    
    def check_name_exists(self, db: Session, name: str, exclude_id: Optional[str] = None) -> bool:
        """Check if company name exists (excluding specific ID)."""
        query = db.query(CompanyModel).filter(
            func.lower(CompanyModel.name) == name.lower().strip()
        )
        
        if exclude_id:
            query = query.filter(CompanyModel.id != exclude_id)
        
        return query.first() is not None
    
    def check_email_exists(self, db: Session, email: str, exclude_id: Optional[str] = None) -> bool:
        """Check if company email exists (excluding specific ID)."""
        if not email:
            return False
        
        query = db.query(CompanyModel).filter(
            func.lower(CompanyModel.email_address) == email.lower().strip()
        )
        
        if exclude_id:
            query = query.filter(CompanyModel.id != exclude_id)
        
        return query.first() is not None
    
    def check_website_exists(self, db: Session, website_url: str, exclude_id: Optional[str] = None) -> bool:
        """Check if company website exists (excluding specific ID)."""
        if not website_url:
            return False
        
        query = db.query(CompanyModel).filter(
            func.lower(CompanyModel.website_url) == website_url.lower().strip()
        )
        
        if exclude_id:
            query = query.filter(CompanyModel.id != exclude_id)
        
        return query.first() is not None
    
    def get_companies_with_job_descriptions(self, db: Session) -> List[CompanyModel]:
        """Get companies that have associated job descriptions."""
        return db.query(CompanyModel).join(
            CompanyModel.job_descriptions
        ).distinct().all()
    
    def has_job_descriptions(self, db: Session, company_id: str) -> bool:
        """Check if company has associated job descriptions."""
        company = self.get_by_id(db, company_id)
        if company:
            return len(company.job_descriptions) > 0
        return False
