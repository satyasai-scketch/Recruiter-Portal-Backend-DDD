import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from app.services.jd_template import JDTemplateService
from app.utils.file_loader import JDFileLoader
from app.core.config import settings

async def load_templates_from_directory():
    """Load all JD templates from the configured directory"""
    service = JDTemplateService()
    
    try:
        # Load all templates from directory
        print(f"Loading templates from: {settings.TEMPLATE_DATA_DIR}")
        templates = JDFileLoader.load_from_directory(settings.TEMPLATE_DATA_DIR)
        
        if not templates:
            print("No templates found")
            return
        
        print(f"Found {len(templates)} templates to process")
        
        # Add each template
        success_count = 0
        fail_count = 0
        
        for template in templates:
            success = await service.add_template(template)
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\nResults: {success_count} added, {fail_count} failed")
        
    except Exception as e:
        print(f"Error: {e}")

async def load_templates_from_file(file_path: str):
    """Load templates from a specific file"""
    service = JDTemplateService()
    
    try:
        print(f"Loading templates from: {file_path}")
        templates = JDFileLoader.load_from_json_file(file_path)
        
        print(f"Found {len(templates)} templates")
        
        for template in templates:
            await service.add_template(template)
        
        print("Loading complete")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Default: load from directory
    asyncio.run(load_templates_from_directory())
    
    # Or load from specific file:
    # asyncio.run(load_templates_from_file("path/to/file.json"))