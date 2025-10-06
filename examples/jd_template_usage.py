"""
Example usage of JD Template Service
"""
import asyncio
from app.services.jd_template import JDTemplateService
from app.utils.file_loader import JDFileLoader

async def example_add_single_template():
    """Example: Add a single template"""
    service = JDTemplateService()
    
    jd_data = {
        "title": "Senior Python Developer",
        "requirements": ["5+ years Python", "Django/FastAPI", "PostgreSQL"],
        "responsibilities": ["Design APIs", "Mentor juniors"],
        "level": "senior"
    }
    
    success = await service.add_template(jd_data)
    print(f"Template added: {success}")

async def example_add_from_file():
    """Example: Add templates from file"""
    service = JDTemplateService()
    
    # Load from file
    templates = JDFileLoader.load_from_json_file("data/jd_templates/jd_templates2.json")
    
    # Add each template
    for template in templates:
        await service.add_template(template)

async def example_find_best_match():
    """Example: Find best matching template for JD enhancement"""
    service = JDTemplateService()
    
    # User's rough JD
    user_jd = {
        "title": "Python Developer",
        "requirements": ["Python", "Web development", "Database"],
        "experience_years": 3
    }
    
    # Find best match
    best_match = await service.find_best_match(user_jd, min_similarity=0.5)
    print(f"Best match found: {best_match is not None}")
    print(best_match)
    if best_match:
        print(f"Best match: {best_match.get('title')}")
        print(f"Requirements: {best_match.get('requirements')}")
        # Use best_match to enhance user's JD
    else:
        print("No suitable match found")

async def example_find_top_matches():
    """Example: Find top 3 similar templates"""
    service = JDTemplateService()
    
    user_jd = {"title": "Backend Developer", "skills": ["Python", "APIs"]}
    
    top_matches = await service.find_top_matches(user_jd, top_k=3, min_similarity=0.6)
    
    for i, match in enumerate(top_matches, 1):
        print(f"{i}. {match['template'].get('title')} (similarity: {match['similarity']})")

if __name__ == "__main__":
    # Run examples
    asyncio.run(example_add_from_file())