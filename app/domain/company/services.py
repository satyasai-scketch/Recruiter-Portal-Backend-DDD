# app/domain/company/services.py
from typing import Optional
from datetime import datetime
from uuid import uuid4

from .entities import Company, CompanyAddress, SocialMediaLinks
from .rules import CompanyBusinessRules

def create_company(
    name: str,
    website_url: Optional[str] = None,
    contact_number: Optional[str] = None,
    email_address: Optional[str] = None,
    street: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    pincode: Optional[str] = None,
    twitter_link: Optional[str] = None,
    instagram_link: Optional[str] = None,
    facebook_link: Optional[str] = None,
    linkedin_link: Optional[str] = None,
    about_company: Optional[str] = None,
    created_by: Optional[str] = None
) -> Company:
    """Create a new company with validation."""
    
    # Create address if any address fields are provided
    address = None
    if any([street, city, state, country, pincode]):
        address = CompanyAddress(
            street=street,
            city=city,
            state=state,
            country=country,
            pincode=pincode
        )
    
    # Create social media links if any are provided
    social_media = None
    if any([twitter_link, instagram_link, facebook_link, linkedin_link]):
        social_media = SocialMediaLinks(
            twitter_link=twitter_link,
            instagram_link=instagram_link,
            facebook_link=facebook_link,
            linkedin_link=linkedin_link
        )
    
    # Create company entity
    company = Company(
        id=str(uuid4()),
        name=name,
        website_url=website_url,
        contact_number=contact_number,
        email_address=email_address,
        address=address,
        social_media=social_media,
        about_company=about_company,
        created_at=datetime.now(),
        created_by=created_by,
        updated_at=datetime.now(),
        updated_by=created_by
    )
    
    # Validate company data
    validation_errors = CompanyBusinessRules.is_valid_company_data(company)
    if validation_errors:
        raise ValueError(f"Company validation failed: {', '.join(validation_errors)}")
    
    return company

def update_company(
    existing_company: Company,
    name: Optional[str] = None,
    website_url: Optional[str] = None,
    contact_number: Optional[str] = None,
    email_address: Optional[str] = None,
    street: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    pincode: Optional[str] = None,
    twitter_link: Optional[str] = None,
    instagram_link: Optional[str] = None,
    facebook_link: Optional[str] = None,
    linkedin_link: Optional[str] = None,
    about_company: Optional[str] = None,
    updated_by: Optional[str] = None
) -> Company:
    """Update an existing company with validation."""
    
    # Update basic fields
    updated_name = name if name is not None else existing_company.name
    updated_website_url = website_url if website_url is not None else existing_company.website_url
    updated_contact_number = contact_number if contact_number is not None else existing_company.contact_number
    updated_email_address = email_address if email_address is not None else existing_company.email_address
    updated_about_company = about_company if about_company is not None else existing_company.about_company
    
    # Update address
    updated_address = existing_company.address
    if any([street, city, state, country, pincode]):
        updated_address = CompanyAddress(
            street=street if street is not None else (existing_company.address.street if existing_company.address else None),
            city=city if city is not None else (existing_company.address.city if existing_company.address else None),
            state=state if state is not None else (existing_company.address.state if existing_company.address else None),
            country=country if country is not None else (existing_company.address.country if existing_company.address else None),
            pincode=pincode if pincode is not None else (existing_company.address.pincode if existing_company.address else None)
        )
    
    # Update social media
    updated_social_media = existing_company.social_media
    if any([twitter_link, instagram_link, facebook_link, linkedin_link]):
        updated_social_media = SocialMediaLinks(
            twitter_link=twitter_link if twitter_link is not None else (existing_company.social_media.twitter_link if existing_company.social_media else None),
            instagram_link=instagram_link if instagram_link is not None else (existing_company.social_media.instagram_link if existing_company.social_media else None),
            facebook_link=facebook_link if facebook_link is not None else (existing_company.social_media.facebook_link if existing_company.social_media else None),
            linkedin_link=linkedin_link if linkedin_link is not None else (existing_company.social_media.linkedin_link if existing_company.social_media else None)
        )
    
    # Create updated company
    updated_company = Company(
        id=existing_company.id,
        name=updated_name,
        website_url=updated_website_url,
        contact_number=updated_contact_number,
        email_address=updated_email_address,
        address=updated_address,
        social_media=updated_social_media,
        about_company=updated_about_company,
        created_at=existing_company.created_at,
        created_by=existing_company.created_by,
        updated_at=datetime.now(),
        updated_by=updated_by
    )
    
    # Validate updated company data
    validation_errors = CompanyBusinessRules.is_valid_company_data(updated_company)
    if validation_errors:
        raise ValueError(f"Company validation failed: {', '.join(validation_errors)}")
    
    return updated_company

def validate_company_uniqueness(
    companies: list,
    name: str,
    email_address: Optional[str] = None,
    website_url: Optional[str] = None,
    exclude_id: Optional[str] = None
) -> None:
    """Validate that company data is unique within the system."""
    
    # Check name uniqueness
    if not CompanyBusinessRules.validate_company_name_uniqueness(companies, name, exclude_id):
        raise ValueError("Company name must be unique")
    
    # Check email uniqueness
    if email_address and not CompanyBusinessRules.validate_company_email_uniqueness(companies, email_address, exclude_id):
        raise ValueError("Company email address must be unique")
    
    # Check website uniqueness
    if website_url and not CompanyBusinessRules.validate_company_website_uniqueness(companies, website_url, exclude_id):
        raise ValueError("Company website URL must be unique")
