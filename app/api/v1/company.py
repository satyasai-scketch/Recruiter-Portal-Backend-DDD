# app/api/v1/company.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_db, get_current_user
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyRead,
    CompanyAddressRead,
    CompanySocialMediaRead,
    CompanyListResponse,
    CompanySearchRequest,
    CompanyResponse
)
from app.cqrs.handlers import handle_command, handle_query
from app.cqrs.commands.company_commands import CreateCompany, UpdateCompany, DeleteCompany
from app.cqrs.queries.company_queries import (
    GetCompany,
    GetCompanyByName,
    ListCompanies,
    SearchCompanies,
    CountCompanies,
    CountSearchCompanies
)
from app.domain.company.rules import CompanyBusinessRules

router = APIRouter()

def _convert_model_to_read_schema(company_model) -> CompanyRead:
    """Convert CompanyModel to CompanyRead schema format."""
    # Build address object if any address fields exist
    address = None
    if any([company_model.street, company_model.city, company_model.state, 
            company_model.country, company_model.pincode]):
        address = CompanyAddressRead(
            street=company_model.street,
            city=company_model.city,
            state=company_model.state,
            country=company_model.country,
            pincode=company_model.pincode
        )
    
    # Build social media object if any social media fields exist
    social_media = None
    if any([company_model.twitter_link, company_model.instagram_link, 
            company_model.facebook_link]):
        social_media = CompanySocialMediaRead(
            twitter_link=company_model.twitter_link,
            instagram_link=company_model.instagram_link,
            facebook_link=company_model.facebook_link
        )
    
    return CompanyRead(
        id=company_model.id,
        name=company_model.name,
        website_url=company_model.website_url,
        contact_number=company_model.contact_number,
        email_address=company_model.email_address,
        about_company=company_model.about_company,
        address=address,
        social_media=social_media,
        created_at=company_model.created_at,
        created_by=company_model.created_by,
        updated_at=company_model.updated_at,
        updated_by=company_model.updated_by
    )

@router.post("/", response_model=CompanyRead, summary="Create Company")
async def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Create a new company.
    
    - **name**: Company name (required)
    - **website_url**: Company website URL (optional)
    - **contact_number**: Contact phone number (optional)
    - **email_address**: Company email address (optional)
    - **address**: Company address information (optional)
    - **social_media**: Social media links (optional)
    - **about_company**: Company description (optional)
    """
    try:
        # Convert Pydantic model to dict and add user info
        payload = company_data.model_dump()
        payload["created_by"] = user.id
        payload["updated_by"] = user.id
        
        # Flatten address and social_media if present
        if payload.get("address"):
            address_data = payload.pop("address")
            payload.update(address_data)
        
        if payload.get("social_media"):
            social_data = payload.pop("social_media")
            payload.update(social_data)
        
        # Create company using CQRS
        created_company = handle_command(db, CreateCompany(payload))
        
        # Convert database model to schema format
        return _convert_model_to_read_schema(created_company)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{company_id}", response_model=CompanyRead, summary="Get Company by ID")
async def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get company information by ID.
    """
    company = handle_query(db, GetCompany(company_id))
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return _convert_model_to_read_schema(company)

@router.get("/name/{company_name}", response_model=CompanyRead, summary="Get Company by Name")
async def get_company_by_name(
    company_name: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get company information by name.
    """
    company = handle_query(db, GetCompanyByName(company_name))
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return _convert_model_to_read_schema(company)

@router.get("/", response_model=CompanyListResponse, summary="List Companies")
async def list_companies(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    List all companies with pagination.
    """
    skip = (page - 1) * size
    
    # Get companies and total count
    companies = handle_query(db, ListCompanies(skip, size))
    total = handle_query(db, CountCompanies())
    
    # Convert to response format
    company_reads = [_convert_model_to_read_schema(company) for company in companies]
    
    return CompanyListResponse(
        companies=company_reads,
        total=total,
        page=page,
        size=size,
        has_next=(skip + size) < total,
        has_prev=page > 1
    )

@router.post("/search", response_model=CompanyListResponse, summary="Search Companies")
async def search_companies(
    search_request: CompanySearchRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Search companies based on criteria.
    
    - **name**: Search by company name (optional)
    - **city**: Search by city (optional)
    - **country**: Search by country (optional)
    - **page**: Page number (default: 1)
    - **size**: Page size (default: 10)
    """
    skip = (search_request.page - 1) * search_request.size
    
    # Build search criteria
    search_criteria = CompanyBusinessRules.get_company_search_criteria(
        name=search_request.name,
        city=search_request.city,
        country=search_request.country
    )
    
    # Get companies and total count
    companies = handle_query(db, SearchCompanies(search_criteria, skip, search_request.size))
    total = handle_query(db, CountSearchCompanies(search_criteria))
    
    # Convert to response format
    company_reads = [_convert_model_to_read_schema(company) for company in companies]
    
    return CompanyListResponse(
        companies=company_reads,
        total=total,
        page=search_request.page,
        size=search_request.size,
        has_next=(skip + search_request.size) < total,
        has_prev=search_request.page > 1
    )

@router.put("/{company_id}", response_model=CompanyRead, summary="Update Company")
async def update_company(
    company_id: str,
    company_data: CompanyUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Update company information.
    
    All fields are optional. Only provided fields will be updated.
    """
    try:
        # Convert Pydantic model to dict and add user info
        payload = company_data.model_dump(exclude_unset=True)
        payload["updated_by"] = user.id
        
        # Flatten address and social_media if present
        if payload.get("address"):
            address_data = payload.pop("address")
            payload.update(address_data)
        
        if payload.get("social_media"):
            social_data = payload.pop("social_media")
            payload.update(social_data)
        
        # Update company using CQRS
        updated_company = handle_command(db, UpdateCompany(company_id, payload))
        
        if not updated_company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return _convert_model_to_read_schema(updated_company)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{company_id}", response_model=CompanyResponse, summary="Delete Company")
async def delete_company(
    company_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Delete a company.
    
    Company cannot be deleted if it has associated job descriptions.
    """
    try:
        # Delete company using CQRS
        success = handle_command(db, DeleteCompany(company_id))
        
        if not success:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return CompanyResponse(
            message="Company deleted successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
