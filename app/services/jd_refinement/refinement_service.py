from typing import Optional, Dict, Any, Union
from app.schemas.jd import JDRefinementResponse
from app.services.jd_template import JDTemplateService
from app.core.config import settings
from .base import AIRefinerService
from .openai_refiner import OpenAIRefinerService
from .prompt_templates import JDPromptTemplates


class JDRefinementService:
    """
    Main service for JD refinement/enhancement.
    Provides two approaches:
    1. Direct AI refinement
    2. Template-based refinement
    """
    
    def __init__(
        self,
        ai_service: Optional[AIRefinerService] = None,
        template_service: Optional[JDTemplateService] = None
    ):
        """Initialize with optional dependency injection"""
        self.ai_service = ai_service or OpenAIRefinerService(
            api_key=settings.OPENAI_API_KEY,
            model=getattr(settings, "JD_REFINEMENT_MODEL", "gpt-4-turbo-preview"),
            temperature=getattr(settings, "JD_REFINEMENT_TEMPERATURE", 0.7)
        )
        
        self.template_service = template_service or JDTemplateService()
    
    def _convert_company_to_dict(self, company_info: Any) -> Dict[str, Any]:
        """Convert company info object to dict for prompt templates"""
        if isinstance(company_info, dict):
            return company_info
        
        # Convert object attributes to dict
        company_dict = {
            'name': getattr(company_info, 'name', 'N/A'),
            'website_url': getattr(company_info, 'website_url', None),
            'contact_number': getattr(company_info, 'contact_number', None),
            'email_address': getattr(company_info, 'email_address', None),
            'about_company': getattr(company_info, 'about_company', None),
        }
        
        # Handle nested address
        address = getattr(company_info, 'address', None)
        if address:
            company_dict['address'] = {
                'street': getattr(address, 'street', None),
                'city': getattr(address, 'city', None),
                'state': getattr(address, 'state', None),
                'country': getattr(address, 'country', None),
                'pincode': getattr(address, 'pincode', None),
            }
        else:
            company_dict['address'] = {}
        
        # Handle nested social media
        social = getattr(company_info, 'social_media', None)
        if social:
            company_dict['social_media'] = {
                'twitter_link': getattr(social, 'twitter_link', None),
                'instagram_link': getattr(social, 'instagram_link', None),
                'facebook_link': getattr(social, 'facebook_link', None),
            }
        else:
            company_dict['social_media'] = {}
        
        return company_dict
    
    async def refine_direct(
        self,
        jd_text: str,
        role: str,
        company_info: Any
    ) -> JDRefinementResponse:
        """
        Method 1: Direct AI refinement without template matching.
        
        Args:
            jd_text: Original JD text from user
            role: Job role/title
            company_info: Company information (object or dict)
            
        Returns:
            JDRefinementResponse with refined JD
        """
        try:
            print(f"🔄 Starting direct refinement for role: {role}")
            
            # Convert company info to dict
            company_dict = self._convert_company_to_dict(company_info)
            
            # Generate prompt
            prompt = JDPromptTemplates.direct_refinement_prompt(
                jd_text=jd_text,
                role=role,
                company_info=company_dict
            )
            
            # Get AI refinement
            refined_jd = await self.ai_service.refine_with_prompt(prompt)
            
            # Extract improvements
            improvements = await self.ai_service.extract_improvements(
                original=jd_text,
                refined=refined_jd
            )
            
            print(f"✓ Direct refinement complete")
            
            return JDRefinementResponse(
                jd_id="",  # Will be set by caller
                original_text=jd_text,
                refined_text=refined_jd,
                improvements=improvements,
                methodology="direct",
                template_used=None,
                template_similarity=None
            )
            
        except Exception as e:
            print(f"✗ Error in direct refinement: {e}")
            raise
    
    async def refine_with_template(
        self,
        jd_text: str,
        role: str,
        company_info: Any,
        min_similarity: float = 0.7
    ) -> JDRefinementResponse:
        """
        Method 2: Template-based refinement using best matching template.
        
        Args:
            jd_text: Original JD text from user
            role: Job role/title
            company_info: Company information (object or dict)
            min_similarity: Minimum similarity threshold for template matching
            
        Returns:
            JDRefinementResponse with refined JD using template
        """
        try:
            print(f"🔄 Starting template-based refinement for role: {role}")
            
            # Convert company info to dict
            company_dict = self._convert_company_to_dict(company_info)
            
            # Step 1: Find best matching template
            print(f"  → Searching for matching template (min similarity: {min_similarity})")
            
            best_template = await self.template_service.find_best_match(
                user_jd_input=jd_text,
                min_similarity=min_similarity
            )
            
            if not best_template:
                print(f"  ⚠ No template found above {min_similarity} threshold")
                print(f"  → Falling back to direct refinement")
                return await self.refine_direct(jd_text, role, company_info)
            
            # Get similarity score from search
            query_vector = await self.template_service.embedding_service.embed_text(jd_text)
            matches = await self.template_service.storage_service.search_similar(
                query_vector=query_vector,
                top_k=1,
                min_score=min_similarity
            )
            similarity_score = matches[0]['score'] if matches else 0.0
            
            print(f"  ✓ Found template: {best_template.get('title')} (similarity: {similarity_score:.1%})")
            
            # Step 2: Generate prompt with template
            prompt = JDPromptTemplates.template_based_refinement_prompt(
                jd_text=jd_text,
                role=role,
                company_info=company_dict,
                template=best_template,
                similarity_score=similarity_score
            )
            
            # Step 3: Get AI refinement
            print(f"  → Generating refined JD using template")
            refined_jd = await self.ai_service.refine_with_prompt(prompt)
            
            # Step 4: Extract improvements
            improvements = await self.ai_service.extract_improvements(
                original=jd_text,
                refined=refined_jd
            )
            
            print(f"✓ Template-based refinement complete")
            
            return JDRefinementResponse(
                jd_id="",  # Will be set by caller
                original_text=jd_text,
                refined_text=refined_jd,
                improvements=improvements,
                methodology="template_based",
                template_used=best_template,
                template_similarity=similarity_score
            )
            
        except Exception as e:
            print(f"✗ Error in template-based refinement: {e}")
            raise
    
    async def refine_auto(
        self,
        jd_text: str,
        role: str,
        company_info: Any,
        prefer_template: bool = True,
        min_similarity: float = 0.7
    ) -> JDRefinementResponse:
        """
        Auto-select best refinement method.
        
        Args:
            jd_text: Original JD text
            role: Job role
            company_info: Company information
            prefer_template: If True, try template-based first
            min_similarity: Threshold for template matching
            
        Returns:
            JDRefinementResponse
        """
        if prefer_template:
            return await self.refine_with_template(
                jd_text, role, company_info, min_similarity
            )
        else:
            return await self.refine_direct(jd_text, role, company_info)