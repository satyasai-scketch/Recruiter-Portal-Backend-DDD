from typing import Dict, Any

class JDPromptTemplates:
    """Centralized prompt templates for JD refinement"""
    @staticmethod
    def _format_company_context(company: dict) -> str:
        """Format company info for prompt context"""
        if not company or not company.get('name') or company.get('name') == 'Not specified':
            return """
    **Company Information:** Not provided

    Note: Generic company context will be used for refinement.
    """
        
        address = company.get('address', {}) or {}
        
        return f"""
    **Company Information:**
    - Name: {company.get('name', 'N/A')}
    - Industry/About: {company.get('about_company', 'N/A')[:200]}
    - Location: {address.get('city', 'N/A')}, {address.get('country', 'N/A')}
    - Website: {company.get('website_url', 'N/A')}
    """
    
    @staticmethod
    def direct_refinement_prompt(notes: str,jd_text: str, role: str, company_info: Dict[str, Any]) -> str:
        """Generate prompt for direct JD refinement"""
        
        company_context = JDPromptTemplates._format_company_context(company_info)
        
        # Adjust prompt based on whether company info exists
        company_name = company_info.get('name', 'the company') if company_info else 'the company'
        
        prompt = f"""You are an expert HR consultant specializing in job description refinement.

    {company_context}

    **Role:** {role}

    **Original Job Description:**
    {jd_text}
    **Please incorporate the following notes when refining the job description:**
    {notes}
    **Your Task:**
    FIRST, analyze if the provided text is a valid job description or contains JD-related content.

    - **IF the text is a valid/partial JD**: Refine and enhance it to make it:
    1. **Clear & Professional**: Remove ambiguity, improve structure
    2. **Compelling**: Make it attractive to top talent
    3. **Complete**: Ensure all key sections are present
    4. **Keyword-Optimized**: Include relevant technical terms
    5. **Action-Oriented**: Use strong action verbs
    6. **Inclusive**: Use gender-neutral, inclusive language
    7. Consider 

    - **IF the text is irrelevant/not a JD** (e.g., random text, unrelated content, gibberish):
    Generate a complete professional job description from scratch for the role "{role}" based on industry standards and the company information provided above.

    **Output Format:**
    Provide a well-structured JD. Use sections that make sense for this role. Common sections include:
    - Job Title
    - About the Role / Role Overview
    - Key Responsibilities / What You'll Do
    - Required Qualifications / Must-Have Skills
    - Preferred Qualifications / Nice-to-Have Skills
    - Technical Skills (if applicable)
    - What We Offer / Benefits / Perks
    - Work Environment / Team Structure (if relevant)
    {"- About " + company_name if company_name != 'the company' else "- About the Company"}
    - Application Process / Next Steps (optional)

    **Important:** 
    - Maintain core requirements and intent
    - Don't add unrealistic requirements
    - Keep it concise but comprehensive
    - Use your judgment to decide: refine or generate from scratch
    - Add, remove, or rename sections as appropriate for the role and industry
    - Don't mention this decision-making process in the output
    - Take the notes provided into consideration without fail
    """
        return prompt

    @staticmethod
    def template_based_refinement_prompt(
        jd_text: str,
        role: str,
        company_info: Dict[str, Any],
        template: Dict[str, Any],
        similarity_score: float
    ) -> str:
        """Generate prompt for template-based refinement"""
        
        company_context = JDPromptTemplates._format_company_context(company_info)
        company_name = company_info.get('name', 'the company') if company_info else 'the company'
        
        template_info = f"""
    **Standard Template (Similarity: {similarity_score:.1%}):**
    - Title: {template.get('title', 'N/A')}
    - Level: {template.get('level', 'N/A')}
    - Domain: {template.get('domain', 'N/A')}
    - Skills Required: {', '.join(template.get('skills', {}).get('technical', [])[:10])}
    """
        
        prompt = f"""You are an expert HR consultant specializing in job description refinement using industry-standard templates.

    {company_context}

    **Role:** {role}

    {template_info}

    **User's Original JD:**
    {jd_text}

    **Your Task:**
    Refine the user's JD by intelligently merging it with the standard template:

    1. **Preserve User Intent**: Keep core requirements from original
    2. **Fill Gaps**: Use template to add missing sections
    3. **Enhance Structure**: Adopt template's professional structure
    4. **Improve Clarity**: Use template's clear language style
    5. **Add Standards**: Include standard skills/requirements from template
    6. **Customize**: Adapt everything to fit {"" if company_name == 'the company' else company_name + "'s "}context

    **Output Format:**
    - Job Title
    - About the Role
    - Key Responsibilities
    - Required Qualifications  
    - Preferred Qualifications
    - Skills Required
    - What We Offer
    {"- About " + company_name if company_name != 'the company' else ""}

    **Important:**
    - Intelligently merge, don't just copy template
    - Maintain user's specific requirements
    """
        return prompt
    
    @staticmethod
    def extract_improvements_prompt(original: str, refined: str) -> str:
        """Generate prompt to extract what was improved"""
        
        prompt = f"""
You are a strict JSON generator.

Compare the original and refined job descriptions and identify 3-4 key improvements.

Return ONLY a valid JSON array of strings with NO explanation, NO markdown, and NO extra text.

Original:
{original}

Refined:
{refined}

If the original was invalid/not a JD** (e.g., random text, unrelated content, gibberish) and a JD was generated from scratch, include that as the first improvement like:
["Generated complete professional JD from scratch (+100%)"]

Otherwise Focus on:
- Structural improvements
- Added sections or details
- Clarity enhancements
- Keyword optimization
- Inclusivity improvements

Each string should include a short metric, e.g.:
["Added technical skills section (+1)", "Improved clarity (+30%)", "Enhanced inclusivity (+40%)"]
"""
        return prompt