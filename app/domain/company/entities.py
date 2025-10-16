# app/domain/company/entities.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass(frozen=True)
class CompanyAddress:
    """Value object for company address information."""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    
    def __post_init__(self):
        """Validate address fields."""
        if self.street and len(self.street.strip()) == 0:
            raise ValueError("Street cannot be empty if provided")
        if self.city and len(self.city.strip()) == 0:
            raise ValueError("City cannot be empty if provided")
        if self.state and len(self.state.strip()) == 0:
            raise ValueError("State cannot be empty if provided")
        if self.country and len(self.country.strip()) == 0:
            raise ValueError("Country cannot be empty if provided")
        if self.pincode and len(self.pincode.strip()) == 0:
            raise ValueError("Pincode cannot be empty if provided")

@dataclass(frozen=True)
class SocialMediaLinks:
    """Value object for social media links."""
    twitter_link: Optional[str] = None
    instagram_link: Optional[str] = None
    facebook_link: Optional[str] = None
    linkedin_link: Optional[str] = None
    
    def __post_init__(self):
        """Validate social media links."""
        for field_name, link in [
            ("twitter_link", self.twitter_link),
            ("instagram_link", self.instagram_link),
            ("facebook_link", self.facebook_link),
            ("linkedin_link", self.linkedin_link)
        ]:
            if link and not self._is_valid_url(link):
                raise ValueError(f"{field_name} must be a valid URL")
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Basic URL validation."""
        return url.startswith(('http://', 'https://'))

@dataclass
class Company:
    """Company aggregate root."""
    id: str
    name: str
    website_url: Optional[str] = None
    contact_number: Optional[str] = None
    email_address: Optional[str] = None
    address: Optional[CompanyAddress] = None
    social_media: Optional[SocialMediaLinks] = None
    about_company: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    
    def __post_init__(self):
        """Validate company data."""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Company name is required")
        
        if len(self.name.strip()) > 200:
            raise ValueError("Company name cannot exceed 200 characters")
        
        if self.website_url and not self._is_valid_url(self.website_url):
            raise ValueError("Website URL must be a valid URL")
        
        if self.email_address and not self._is_valid_email(self.email_address):
            raise ValueError("Email address must be valid")
        
        if self.contact_number and len(self.contact_number.strip()) == 0:
            raise ValueError("Contact number cannot be empty if provided")
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Basic URL validation."""
        return url.startswith(('http://', 'https://'))
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Basic email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def update_contact_info(self, website_url: Optional[str] = None, 
                          contact_number: Optional[str] = None,
                          email_address: Optional[str] = None) -> 'Company':
        """Update company contact information."""
        return Company(
            id=self.id,
            name=self.name,
            website_url=website_url if website_url is not None else self.website_url,
            contact_number=contact_number if contact_number is not None else self.contact_number,
            email_address=email_address if email_address is not None else self.email_address,
            address=self.address,
            social_media=self.social_media,
            about_company=self.about_company,
            created_at=self.created_at,
            created_by=self.created_by,
            updated_at=datetime.now(),
            updated_by=self.updated_by
        )
    
    def update_address(self, address: CompanyAddress) -> 'Company':
        """Update company address."""
        return Company(
            id=self.id,
            name=self.name,
            website_url=self.website_url,
            contact_number=self.contact_number,
            email_address=self.email_address,
            address=address,
            social_media=self.social_media,
            about_company=self.about_company,
            created_at=self.created_at,
            created_by=self.created_by,
            updated_at=datetime.now(),
            updated_by=self.updated_by
        )
    
    def update_social_media(self, social_media: SocialMediaLinks) -> 'Company':
        """Update company social media links."""
        return Company(
            id=self.id,
            name=self.name,
            website_url=self.website_url,
            contact_number=self.contact_number,
            email_address=self.email_address,
            address=self.address,
            social_media=social_media,
            about_company=self.about_company,
            created_at=self.created_at,
            created_by=self.created_by,
            updated_at=datetime.now(),
            updated_by=self.updated_by
        )
    
    def update_about(self, about_company: str) -> 'Company':
        """Update company description."""
        return Company(
            id=self.id,
            name=self.name,
            website_url=self.website_url,
            contact_number=self.contact_number,
            email_address=self.email_address,
            address=self.address,
            social_media=self.social_media,
            about_company=about_company,
            created_at=self.created_at,
            created_by=self.created_by,
            updated_at=datetime.now(),
            updated_by=self.updated_by
        )
