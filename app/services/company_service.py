# app/services/company_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.company_repo import CompanyRepository
from app.domain.company.entities import Company, CompanyAddress, SocialMediaLinks
from app.domain.company.services import (
    create_company as create_company_domain,
    update_company as update_company_domain,
    validate_company_uniqueness
)
from app.domain.company.rules import CompanyBusinessRules
from app.db.models.company import CompanyModel
from app.events.company_events import CompanyCreatedEvent, CompanyUpdatedEvent, CompanyDeletedEvent
from app.events.event_bus import event_bus

class CompanyService:
    """Application service for Company operations."""
    
    def __init__(self):
        self.repo = CompanyRepository()
    
    def create(self, db: Session, data: dict) -> CompanyModel:
        """Create a new company."""
        try:
            # Extract data for domain service
            name = data.get("name")
            website_url = data.get("website_url")
            contact_number = data.get("contact_number")
            email_address = data.get("email_address")
            street = data.get("street")
            city = data.get("city")
            state = data.get("state")
            country = data.get("country")
            pincode = data.get("pincode")
            twitter_link = data.get("twitter_link")
            instagram_link = data.get("instagram_link")
            facebook_link = data.get("facebook_link")
            linkedin_link = data.get("linkedin_link")
            about_company = data.get("about_company")
            created_by = data.get("created_by")
            
            # Get all existing companies for uniqueness validation
            existing_companies = self.repo.get_all(db)
            existing_companies_domain = [self._model_to_domain(company) for company in existing_companies]
            
            # Validate uniqueness
            validate_company_uniqueness(
                existing_companies_domain,
                name,
                email_address,
                website_url
            )
            
            # Create domain entity
            company_domain = create_company_domain(
                name=name,
                website_url=website_url,
                contact_number=contact_number,
                email_address=email_address,
                street=street,
                city=city,
                state=state,
                country=country,
                pincode=pincode,
                twitter_link=twitter_link,
                instagram_link=instagram_link,
                facebook_link=facebook_link,
                linkedin_link=linkedin_link,
                about_company=about_company,
                created_by=created_by
            )
            
            # Convert to model data
            model_data = self._domain_to_model_data(company_domain)
            
            # Create in database
            created_company = self.repo.create(db, model_data)
            
            # Publish event (with error handling)
            try:
                event_bus.publish_event(CompanyCreatedEvent(
                    company_id=created_company.id,
                    company_name=created_company.name,
                    created_by=created_by
                ))
            except Exception as e:
                # Log the event publishing error but don't fail the operation
                print(f"Failed to publish CompanyCreatedEvent: {e}")
                # Optionally, you could implement event retry logic here
            
            return created_company
            
        except Exception as e:
            # Rollback the database transaction
            db.rollback()
            raise e
    
    def get_by_id(self, db: Session, company_id: str) -> Optional[CompanyModel]:
        """Get company by ID."""
        return self.repo.get_by_id(db, company_id)
    
    def get_by_name(self, db: Session, name: str) -> Optional[CompanyModel]:
        """Get company by name."""
        return self.repo.get_by_name(db, name)
    
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[CompanyModel]:
        """Get all companies with pagination."""
        return self.repo.get_all(db, skip, limit)
    
    def search(self, db: Session, search_criteria: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[CompanyModel]:
        """Search companies based on criteria."""
        return self.repo.search(db, search_criteria, skip, limit)
    
    def count(self, db: Session) -> int:
        """Count total number of companies."""
        return self.repo.count(db)
    
    def count_search(self, db: Session, search_criteria: Dict[str, Any]) -> int:
        """Count companies matching search criteria."""
        return self.repo.count_search(db, search_criteria)
    
    def update(self, db: Session, company_id: str, data: dict) -> Optional[CompanyModel]:
        """Update an existing company."""
        try:
            existing_company = self.repo.get_by_id(db, company_id)
            if not existing_company:
                return None
            
            # Get all existing companies for uniqueness validation
            existing_companies = self.repo.get_all(db)
            existing_companies_domain = [self._model_to_domain(company) for company in existing_companies]
            
            # Extract updated data
            name = data.get("name", existing_company.name)
            website_url = data.get("website_url", existing_company.website_url)
            email_address = data.get("email_address", existing_company.email_address)
            
            # Validate uniqueness
            validate_company_uniqueness(
                existing_companies_domain,
                name,
                email_address,
                website_url,
                exclude_id=company_id
            )
            
            # Convert existing model to domain entity
            existing_company_domain = self._model_to_domain(existing_company)
            
            # Update domain entity
            updated_company_domain = update_company_domain(
                existing_company_domain,
                name=data.get("name"),
                website_url=data.get("website_url"),
                contact_number=data.get("contact_number"),
                email_address=data.get("email_address"),
                street=data.get("street"),
                city=data.get("city"),
                state=data.get("state"),
                country=data.get("country"),
                pincode=data.get("pincode"),
                twitter_link=data.get("twitter_link"),
                instagram_link=data.get("instagram_link"),
                facebook_link=data.get("facebook_link"),
                linkedin_link=data.get("linkedin_link"),
                about_company=data.get("about_company"),
                updated_by=data.get("updated_by")
            )
            
            # Update model with new data
            self._update_model_from_domain(existing_company, updated_company_domain)
            
            # Save to database
            updated_company = self.repo.update(db, existing_company)
            
            # Publish event (with error handling)
            try:
                event_bus.publish_event(CompanyUpdatedEvent(
                    company_id=updated_company.id,
                    company_name=updated_company.name,
                    updated_by=data.get("updated_by")
                ))
            except Exception as e:
                # Log the event publishing error but don't fail the operation
                print(f"Failed to publish CompanyUpdatedEvent: {e}")
                # Optionally, you could implement event retry logic here
            
            return updated_company
            
        except Exception as e:
            # Rollback the database transaction
            db.rollback()
            raise e
    
    def delete(self, db: Session, company_id: str) -> bool:
        """Delete a company."""
        try:
            company = self.repo.get_by_id(db, company_id)
            if not company:
                return False
            
            # Check if company can be deleted
            has_job_descriptions = self.repo.has_job_descriptions(db, company_id)
            company_domain = self._model_to_domain(company)
            
            if not CompanyBusinessRules.can_delete_company(company_domain, has_job_descriptions):
                raise ValueError("Cannot delete company with associated job descriptions")
            
            # Delete company
            success = self.repo.delete(db, company_id)
            
            if success:
                # Publish event (with error handling)
                try:
                    event_bus.publish_event(CompanyDeletedEvent(
                        company_id=company_id,
                        company_name=company.name
                    ))
                except Exception as e:
                    # Log the event publishing error but don't fail the operation
                    print(f"Failed to publish CompanyDeletedEvent: {e}")
                    # Optionally, you could implement event retry logic here
            
            return success
            
        except Exception as e:
            # Rollback the database transaction
            db.rollback()
            raise e
    
    def _model_to_domain(self, model: CompanyModel) -> Company:
        """Convert CompanyModel to Company domain entity."""
        address = None
        if any([model.street, model.city, model.state, model.country, model.pincode]):
            address = CompanyAddress(
                street=model.street,
                city=model.city,
                state=model.state,
                country=model.country,
                pincode=model.pincode
            )
        
        social_media = None
        if any([model.twitter_link, model.instagram_link, model.facebook_link, model.linkedin_link]):
            social_media = SocialMediaLinks(
                twitter_link=model.twitter_link,
                instagram_link=model.instagram_link,
                facebook_link=model.facebook_link,
                linkedin_link=model.linkedin_link
            )
        
        return Company(
            id=model.id,
            name=model.name,
            website_url=model.website_url,
            contact_number=model.contact_number,
            email_address=model.email_address,
            address=address,
            social_media=social_media,
            about_company=model.about_company,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by
        )
    
    def _domain_to_model_data(self, domain: Company) -> dict:
        """Convert Company domain entity to model data dictionary."""
        data = {
            "id": domain.id,
            "name": domain.name,
            "website_url": domain.website_url,
            "contact_number": domain.contact_number,
            "email_address": domain.email_address,
            "about_company": domain.about_company,
            "created_at": domain.created_at,
            "created_by": domain.created_by,
            "updated_at": domain.updated_at,
            "updated_by": domain.updated_by
        }
        
        # Add address fields
        if domain.address:
            data.update({
                "street": domain.address.street,
                "city": domain.address.city,
                "state": domain.address.state,
                "country": domain.address.country,
                "pincode": domain.address.pincode
            })
        
        # Add social media fields
        if domain.social_media:
            data.update({
                "twitter_link": domain.social_media.twitter_link,
                "instagram_link": domain.social_media.instagram_link,
                "facebook_link": domain.social_media.facebook_link,
                "linkedin_link": domain.social_media.linkedin_link
            })
        
        return data
    
    def _update_model_from_domain(self, model: CompanyModel, domain: Company) -> None:
        """Update CompanyModel from Company domain entity."""
        model.name = domain.name
        model.website_url = domain.website_url
        model.contact_number = domain.contact_number
        model.email_address = domain.email_address
        model.about_company = domain.about_company
        model.updated_at = domain.updated_at
        model.updated_by = domain.updated_by
        
        # Update address fields
        if domain.address:
            model.street = domain.address.street
            model.city = domain.address.city
            model.state = domain.address.state
            model.country = domain.address.country
            model.pincode = domain.address.pincode
        else:
            model.street = None
            model.city = None
            model.state = None
            model.country = None
            model.pincode = None
        
        # Update social media fields
        if domain.social_media:
            model.twitter_link = domain.social_media.twitter_link
            model.instagram_link = domain.social_media.instagram_link
            model.facebook_link = domain.social_media.facebook_link
            model.linkedin_link = domain.social_media.linkedin_link
        else:
            model.twitter_link = None
            model.instagram_link = None
            model.facebook_link = None
            model.linkedin_link = None
