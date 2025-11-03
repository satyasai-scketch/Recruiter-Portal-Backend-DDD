# app/core/ai_pricing.py
from decimal import Decimal
from typing import Dict, Tuple

# OpenAI pricing per 1K tokens (as of 2024)
# Format: {model: (input_cost_per_1k, output_cost_per_1k)}
OPENAI_PRICING = {
    # GPT-4o models
    "gpt-4o": (Decimal('0.0025'), Decimal('0.0100')),
    "gpt-4o-mini": (Decimal('0.00015'), Decimal('0.0006')),
    "gpt-5" : (Decimal('0.00125'), Decimal('0.0100')),
    
    # GPT-4 models
    "gpt-4-turbo": (Decimal('0.01'), Decimal('0.03')),
    "gpt-4-turbo-preview": (Decimal('0.01'), Decimal('0.03')),
    "gpt-4": (Decimal('0.03'), Decimal('0.06')),
    
    # GPT-3.5 models
    "gpt-3.5-turbo": (Decimal('0.0015'), Decimal('0.002')),
    "gpt-3.5-turbo-1106": (Decimal('0.0015'), Decimal('0.002')),
    
    # Embedding models
    "text-embedding-3-small": (Decimal('0.00002'), Decimal('0.00002')),
    "text-embedding-3-large": (Decimal('0.00013'), Decimal('0.00013')),
    "text-embedding-ada-002": (Decimal('0.0001'), Decimal('0.0001')),
}

SEVEN_PLACES = Decimal('0.0000001')

def get_model_pricing(model: str) -> Tuple[Decimal, Decimal]:
    """
    Get pricing for a specific model.
    
    Args:
        model: The model name (e.g., 'gpt-4o-mini')
        
    Returns:
        Tuple of (input_cost_per_1k, output_cost_per_1k) in USD
        
    Raises:
        ValueError: If model pricing is not found
    """
    if model not in OPENAI_PRICING:
        # Default to gpt-4o-mini pricing if model not found
        return OPENAI_PRICING["gpt-4o-mini"]
    
    return OPENAI_PRICING[model]

def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Calculate costs for input and output tokens.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: The model name
        
    Returns:
        Tuple of (input_cost, output_cost, total_cost) in USD
    """
    input_rate, output_rate = get_model_pricing(model)
    
    # Calculate costs (divide by 1000 since rates are per 1K tokens)
    # Convert to Decimal to avoid float * Decimal multiplication error
    input_cost = (Decimal(input_tokens) / Decimal('1000')) * input_rate
    output_cost = (Decimal(output_tokens) / Decimal('1000')) * output_rate
    total_cost = input_cost + output_cost
    
    # Round to 7 decimal places
    input_cost = input_cost.quantize(SEVEN_PLACES)
    output_cost = output_cost.quantize(SEVEN_PLACES)
    total_cost = total_cost.quantize(SEVEN_PLACES)
    
    return input_cost, output_cost, total_cost

def get_supported_models() -> list:
    """Get list of all supported models"""
    return list(OPENAI_PRICING.keys())

def add_custom_pricing(model: str, input_rate: Decimal, output_rate: Decimal):
    """
    Add custom pricing for a model.
    
    Args:
        model: The model name
        input_rate: Input cost per 1K tokens
        output_rate: Output cost per 1K tokens
    """
    OPENAI_PRICING[model] = (input_rate, output_rate)
