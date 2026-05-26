import json
import logging
import re
from typing import Dict, Any, Type, TypeVar
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

def parse_structured_output(raw_output: str, model: Type[T]) -> T:
    """
    Safely parses unstructured LLM string output into a strict Pydantic model.
    Applies aggressive sanitization to recover malformed JSON.
    """
    clean = raw_output.strip()
    
    # 1. Strip Markdown Code Blocks
    if "```json" in clean:
        clean = clean.split("```json")[1]
    if "```" in clean:
        clean = clean.split("```")[0]
        
    clean = clean.strip()
    
    # 2. Extract best JSON attempt
    try:
        data = json.loads(clean, strict=False)
    except json.JSONDecodeError as e:
        logger.warning(f"[StructuredParser] Initial JSON decode failed: {e}. Attempting regex recovery...")
        # Attempt to find JSON object via regex if there's trailing/leading text
        match = re.search(r'\{.*\}', clean, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0), strict=False)
            except Exception as inner_e:
                logger.error(f"[StructuredParser] Regex JSON recovery failed: {inner_e}")
                raise ValueError(f"Failed to extract valid JSON from LLM output: {raw_output}") from inner_e
        else:
            raise ValueError(f"No JSON object found in LLM output: {raw_output}") from e
            
    # 3. Pydantic Strict Validation
    try:
        validated_model = model.model_validate(data)
        logger.info(f"[StructuredParser] Successfully validated output against {model.__name__}")
        return validated_model
    except ValidationError as e:
        logger.error(f"[StructuredParser] Pydantic validation failed: {e}")
        raise ValueError(f"Output schema validation failed: {e}") from e
