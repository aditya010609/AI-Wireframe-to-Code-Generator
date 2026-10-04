import json
import re
import logging
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel, ValidationError

from src.schema import UIPageAST
from src.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Result object encapsulating the outcome of AST validation and repair."""
    is_valid: bool
    ast: Optional[UIPageAST] = None
    raw_response: str
    cleaned_json_str: str
    repair_attempted: bool = False
    repair_succeeded: bool = False
    errors: str = ""
    repaired_raw_response: Optional[str] = None


def clean_json_string(raw_text: str) -> str:
    """Strip markdown code fence wrappers (```json ... ```) from raw text."""
    if not raw_text:
        return ""
    text = raw_text.strip()
    # Remove markdown code block fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    return text


def format_pydantic_errors(error: ValidationError) -> str:
    """Format Pydantic ValidationError into a clear readable diagnostic summary."""
    lines = []
    for err in error.errors():
        loc = " -> ".join(str(item) for item in err.get("loc", []))
        msg = err.get("msg", "")
        err_type = err.get("type", "")
        lines.append(f"- Location: [{loc}] | Error: {msg} (type: {err_type})")
    return "\n".join(lines)


def validate_and_repair_ast(
    raw_response: str,
    gemini_client: Optional[GeminiClient] = None
) -> ValidationResult:
    """
    Validate Gemini raw output against UIPageAST schema.
    If validation fails and gemini_client is provided, attempt EXPLICITLY 1 contextual repair.
    
    Returns ValidationResult object.
    """
    cleaned = clean_json_string(raw_response)
    
    # Attempt 1: Standard JSON parsing & Pydantic validation
    json_obj = None
    parse_error = ""
    try:
        json_obj = json.loads(cleaned)
    except Exception as e:
        parse_error = f"JSON Syntax Error: {str(e)}"
    
    if json_obj is not None:
        try:
            validated_ast = UIPageAST.model_validate(json_obj)
            return ValidationResult(
                is_valid=True,
                ast=validated_ast,
                raw_response=raw_response,
                cleaned_json_str=cleaned,
                repair_attempted=False,
                repair_succeeded=False,
                errors=""
            )
        except ValidationError as val_err:
            parse_error = format_pydantic_errors(val_err)

    # Initial validation failed! Check if repair is possible
    logger.warning(f"AST Validation failed. Errors:\n{parse_error}")

    if not gemini_client:
        return ValidationResult(
            is_valid=False,
            ast=None,
            raw_response=raw_response,
            cleaned_json_str=cleaned,
            repair_attempted=False,
            repair_succeeded=False,
            errors=parse_error
        )

    # Attempt 2: Controlled Self-Correction (EXACTLY 1 REPAIR ATTEMPT)
    logger.info("Triggering Controlled Self-Correction Repair (1 attempt)...")
    repaired_raw = ""
    try:
        repaired_raw = gemini_client.repair_ast_json(cleaned, parse_error)
        repaired_cleaned = clean_json_string(repaired_raw)
        repaired_json = json.loads(repaired_cleaned)
        repaired_ast = UIPageAST.model_validate(repaired_json)

        logger.info("Contextual Repair SUCCEEDED!")
        return ValidationResult(
            is_valid=True,
            ast=repaired_ast,
            raw_response=raw_response,
            cleaned_json_str=repaired_cleaned,
            repair_attempted=True,
            repair_succeeded=True,
            errors=parse_error,
            repaired_raw_response=repaired_raw
        )
    except Exception as repair_err:
        repair_fail_msg = f"Original Errors:\n{parse_error}\n\nRepair Failure:\n{str(repair_err)}"
        if isinstance(repair_err, ValidationError):
            repair_fail_msg = f"Original Errors:\n{parse_error}\n\nRepair Pydantic Errors:\n{format_pydantic_errors(repair_err)}"
        
        logger.error("Controlled Self-Correction Repair FAILED.")
        return ValidationResult(
            is_valid=False,
            ast=None,
            raw_response=raw_response,
            cleaned_json_str=cleaned,
            repair_attempted=True,
            repair_succeeded=False,
            errors=repair_fail_msg,
            repaired_raw_response=repaired_raw
        )
