# app/schemas/company.py
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime

class CompanyAddressBase(BaseModel):
    """Base schema for company address."""
    street: Optional[str] = Field(None, max_length=200, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    pincode: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")

class CompanySocialMediaBase(BaseModel):
    """Base schema for company social media links."""
    twitter_link: Optional[str] = Field(None, description="Twitter profile URL")
    instagram_link: Optional[str] = Field(None, description="Instagram profile URL")
    facebook_link: Optional[str] = Field(None, description="Facebook page URL")
    
    @validator('twitter_link', 'instagram_link', 'facebook_link')
    def validate_urls(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class CompanyBase(BaseModel):
    """Base schema for company data."""
    name: str = Field(..., min_length=1, max_length=200, description="Company name")
    website_url: Optional[str] = Field(None, description="Company website URL")
    contact_number: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email_address: Optional[EmailStr] = Field(None, description="Company email address")
    about_company: Optional[str] = Field(None, description="About the company (rich text)")
    
    @validator('website_url')
    def validate_website_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Website URL must start with http:// or https://')
        return v

class CompanyCreate(CompanyBase):
    """Schema for creating a new company."""
    address: Optional[CompanyAddressBase] = None
    social_media: Optional[CompanySocialMediaBase] = None

class CompanyUpdate(BaseModel):
    """Schema for updating company information."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Company name")
    website_url: Optional[str] = Field(None, description="Company website URL")
    contact_number: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email_address: Optional[EmailStr] = Field(None, description="Company email address")
    about_company: Optional[str] = Field(None, description="About the company (rich text)")
    address: Optional[CompanyAddressBase] = None
    social_media: Optional[CompanySocialMediaBase] = None
    
    @validator('website_url')
    def validate_website_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Website URL must start with http:// or https://')
        return v

class CompanyAddressRead(CompanyAddressBase):
    """Schema for reading company address."""
    pass

class CompanySocialMediaRead(CompanySocialMediaBase):
    """Schema for reading company social media links."""
    pass

class CompanyRead(CompanyBase):
    """Schema for reading company information."""
    id: str
    address: Optional[CompanyAddressRead] = None
    social_media: Optional[CompanySocialMediaRead] = None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class CompanyListResponse(BaseModel):
    """Schema for company list response."""
    companies: List[CompanyRead]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool

class CompanySearchRequest(BaseModel):
    """Schema for company search request."""
    name: Optional[str] = Field(None, description="Search by company name")
    city: Optional[str] = Field(None, description="Search by city")
    country: Optional[str] = Field(None, description="Search by country")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Page size")

class CompanyResponse(BaseModel):
    """Schema for company operation response."""
    message: str
    company: Optional[CompanyRead] = None
