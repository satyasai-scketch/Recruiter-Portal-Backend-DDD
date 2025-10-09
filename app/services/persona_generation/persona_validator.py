from typing import Dict, List, Any


class PersonaValidator:
    """Phase 4: Validate and auto-correct persona structure"""
    
    @staticmethod
    def validate_persona(persona: Dict) -> Dict[str, Any]:
        """Validate persona structure and weights"""
        errors = []
        
        if 'categories' not in persona:
            return {'is_valid': False, 'errors': ['Missing categories key']}
        
        categories = persona['categories']
        required_names = [
            'Technical Skills',
            'Cognitive Demands',
            'Values (Schwartz)',
            'Foundational Behaviors',
            'Leadership Skills',
            'Education and Experience'
        ]
        
        # Check all required categories exist
        cat_names = [c.get('name') for c in categories]
        for req_name in required_names:
            if req_name not in cat_names:
                errors.append(f"Missing category: {req_name}")
        
        # Check main weights sum to 100
        main_sum = sum(c.get('weight_percentage', 0) for c in categories)
        if abs(main_sum - 100) > 1:
            errors.append(f"Main category weights sum to {main_sum}, should be 100")
        
        # Check each category's subcategories sum to 100
        for cat in categories:
            cat_name = cat.get('name', 'Unknown')
            subcats = cat.get('subcategories', [])
            subcat_sum = sum(s.get('weight_percentage', 0) for s in subcats)
            if subcats and abs(subcat_sum - 100) > 1:
                errors.append(f"{cat_name} subcategories sum to {subcat_sum}, should be 100")
            
            # Check positions are sequential
            positions = [s.get('position') for s in subcats]
            expected_positions = list(range(1, len(subcats) + 1))
            if positions != expected_positions:
                errors.append(f"{cat_name} positions not sequential: {positions}")
            
            # Check level_id is string
            for i, subcat in enumerate(subcats):
                if 'level_id' in subcat and not isinstance(subcat['level_id'], str):
                    errors.append(f"{cat_name} subcategory {i+1} level_id is not a string")
        
        return {'is_valid': len(errors) == 0, 'errors': errors}
    
    @staticmethod
    def auto_correct_weights(persona: Dict, target_main_weights: Dict) -> Dict:
        """Ensure persona matches calculated weights"""
        if 'categories' not in persona:
            return persona
        
        categories = persona['categories']
        
        # Mapping from display names to internal keys
        name_to_key = {
            'Technical Skills': 'technical',
            'Cognitive Demands': 'cognitive',
            'Values (Schwartz)': 'values',
            'Foundational Behaviors': 'behavioral',
            'Leadership Skills': 'leadership',
            'Education and Experience': 'education_experience'
        }
        
        # Force main weights to match calculated values
        for cat in categories:
            cat_name = cat.get('name')
            if cat_name in name_to_key:
                internal_key = name_to_key[cat_name]
                if internal_key in target_main_weights:
                    cat['weight_percentage'] = target_main_weights[internal_key]
                    # Update range based on new weight
                    new_range = PersonaValidator._calculate_range(target_main_weights[internal_key])
                    cat['range_min'] = new_range[0]
                    cat['range_max'] = new_range[1]
        
        # Fix subcategory weights to integers and ensure sum is 100
        for cat in categories:
            if 'subcategories' not in cat:
                continue
            
            subcats = cat['subcategories']
            subcat_sum = sum(s.get('weight_percentage', 0) for s in subcats)
            
            if subcat_sum > 0:
                # Normalize to 100 and convert to integers
                factor = 100 / subcat_sum
                for i, subcat in enumerate(subcats):
                    subcat['weight_percentage'] = int(round(subcat['weight_percentage'] * factor))
                    subcat['position'] = i + 1
                    
                    # Ensure level_id is string
                    if 'level_id' in subcat and not isinstance(subcat['level_id'], str):
                        subcat['level_id'] = str(subcat['level_id'])
                    
                    # Calculate and set range for subcategory
                    sub_range = PersonaValidator._calculate_range(subcat['weight_percentage'])
                    subcat['range_min'] = sub_range[0]
                    subcat['range_max'] = sub_range[1]
                
                # Fix rounding to ensure sum is exactly 100
                new_sum = sum(s['weight_percentage'] for s in subcats)
                if new_sum != 100 and subcats:
                    difference = 100 - new_sum
                    largest_idx = max(range(len(subcats)), key=lambda i: subcats[i]['weight_percentage'])
                    subcats[largest_idx]['weight_percentage'] += difference
        
        return persona
    
    @staticmethod
    def _calculate_range(weight: int) -> tuple:
        """Calculate range_min and range_max based on weight"""
        range_min = -min(5, max(2, weight // 7))
        range_max = min(10, max(3, weight // 3.5))
        return (range_min, range_max)