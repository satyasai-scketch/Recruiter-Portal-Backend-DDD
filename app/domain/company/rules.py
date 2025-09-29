# app/domain/company/rules.py
from typing import List, Optional
from .entities import Company, CompanyAddress, SocialMediaLinks

class CompanyBusinessRules:
    """Business rules for Company domain."""
    
    @staticmethod
    def validate_company_name_uniqueness(companies: List[Company], name: str, exclude_id: Optional[str] = None) -> bool:
        """Check if company name is unique within the system."""
        for company in companies:
            if company.id != exclude_id and company.name.lower().strip() == name.lower().strip():
                return False
        return True
    
    @staticmethod
    def validate_company_email_uniqueness(companies: List[Company], email: str, exclude_id: Optional[str] = None) -> bool:
        """Check if company email is unique within the system."""
        if not email:
            return True
        
        for company in companies:
            if (company.id != exclude_id and 
                company.email_address and 
                company.email_address.lower().strip() == email.lower().strip()):
                return False
        return True
    
    @staticmethod
    def validate_company_website_uniqueness(companies: List[Company], website: str, exclude_id: Optional[str] = None) -> bool:
        """Check if company website is unique within the system."""
        if not website:
            return True
        
        for company in companies:
            if (company.id != exclude_id and 
                company.website_url and 
                company.website_url.lower().strip() == website.lower().strip()):
                return False
        return True
    
    @staticmethod
    def is_valid_company_data(company: Company) -> List[str]:
        """Validate company data and return list of validation errors."""
        errors = []
        
        # Name validation
        if not company.name or len(company.name.strip()) == 0:
            errors.append("Company name is required")
        elif len(company.name.strip()) > 200:
            errors.append("Company name cannot exceed 200 characters")
        
        # Website URL validation
        if company.website_url and not company._is_valid_url(company.website_url):
            errors.append("Website URL must be a valid URL")
        
        # Email validation
        if company.email_address and not company._is_valid_email(company.email_address):
            errors.append("Email address must be valid")
        
        # Contact number validation
        if company.contact_number and len(company.contact_number.strip()) == 0:
            errors.append("Contact number cannot be empty if provided")
        
        # Address validation
        if company.address:
            address_errors = CompanyBusinessRules._validate_address(company.address)
            errors.extend(address_errors)
        
        # Social media validation
        if company.social_media:
            social_errors = CompanyBusinessRules._validate_social_media(company.social_media)
            errors.extend(social_errors)
        
        return errors
    
    @staticmethod
    def _validate_address(address: CompanyAddress) -> List[str]:
        """Validate address data."""
        errors = []
        
        if address.street and len(address.street.strip()) == 0:
            errors.append("Street cannot be empty if provided")
        
        if address.city and len(address.city.strip()) == 0:
            errors.append("City cannot be empty if provided")
        
        if address.state and len(address.state.strip()) == 0:
            errors.append("State cannot be empty if provided")
        
        if address.country and len(address.country.strip()) == 0:
            errors.append("Country cannot be empty if provided")
        
        if address.pincode and len(address.pincode.strip()) == 0:
            errors.append("Pincode cannot be empty if provided")
        
        return errors
    
    @staticmethod
    def _validate_social_media(social_media: SocialMediaLinks) -> List[str]:
        """Validate social media links."""
        errors = []
        
        for field_name, link in [
            ("Twitter link", social_media.twitter_link),
            ("Instagram link", social_media.instagram_link),
            ("Facebook link", social_media.facebook_link)
        ]:
            if link and not social_media._is_valid_url(link):
                errors.append(f"{field_name} must be a valid URL")
        
        return errors
    
    @staticmethod
    def can_delete_company(company: Company, has_job_descriptions: bool = False) -> bool:
        """Check if company can be deleted."""
        # Company cannot be deleted if it has associated job descriptions
        if has_job_descriptions:
            return False
        
        return True
    
    @staticmethod
    def get_company_search_criteria(name: Optional[str] = None, 
                                  city: Optional[str] = None,
                                  country: Optional[str] = None) -> dict:
        """Get search criteria for company filtering."""
        criteria = {}
        
        if name:
            criteria['name_contains'] = name.lower().strip()
        
        if city:
            criteria['city_contains'] = city.lower().strip()
        
        if country:
            criteria['country_contains'] = country.lower().strip()
        
        return criteria
