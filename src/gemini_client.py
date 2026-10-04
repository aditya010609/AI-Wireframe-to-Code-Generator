import json
import logging
from typing import Dict, Any, Optional, Tuple, Union
from PIL import Image
import io

from google import genai
from google.genai import types

from src.schema import UIPageAST

logger = logging.getLogger(__name__)


SYSTEM_INSTRUCTIONS = """You are an expert Vision AI engineer specializing in UI/UX architecture and web engineering.
Your task is to analyze wireframe images or UI screenshots and convert them into a structured UI Abstract Syntax Tree (AST) strictly following the target JSON schema.

RULES FOR AST GENERATION:
1. Every component MUST have a unique string 'id' (e.g., 'root-container', 'main-header', 'hero-title-1', 'btn-cta').
2. 'type' MUST be one of these exact ComponentType enum strings:
   - Layout: "header", "navbar", "hero", "section", "grid", "flex", "card", "sidebar", "footer", "modal", "form", "container"
   - Typography: "heading", "text", "badge", "stat"
   - Inputs: "button", "input", "select", "checkbox", "radio", "textarea"
   - Media: "image", "icon", "avatar", "table", "list", "nav_item"
3. Store layout and typography visual properties inside 'style' using standard responsive Tailwind CSS utility classes:
   - bg_color: e.g. "bg-slate-900", "bg-white", "bg-indigo-600"
   - text_color: e.g. "text-white", "text-slate-800", "text-slate-400"
   - font_size: e.g. "text-sm", "text-base", "text-xl", "text-3xl", "text-4xl"
   - font_weight: e.g. "font-normal", "font-medium", "font-semibold", "font-bold"
   - padding: e.g. "p-4", "px-6 py-3", "p-8"
   - margin: e.g. "mb-4", "mx-auto", "mt-2"
   - border: e.g. "border border-slate-700 rounded-xl shadow-lg"
   - width: e.g. "w-full", "max-w-4xl"
   - flex_direction: "flex-row" or "flex-col"
   - justify_content: "justify-between", "justify-center", "justify-start"
   - align_items: "items-center", "items-start"
   - gap: "gap-4", "gap-6"
   - grid_cols: "grid-cols-1 md:grid-cols-3"
4. Build a clean, logically nested tree of children. For example, a "hero" section contains a "flex" or "container" child, which contains "heading", "text", and a "flex" button container.
5. Return ONLY a valid JSON object matching the UIPageAST schema. Do NOT include any explanations or conversational text outside the JSON.
"""


class GeminiClient:
    """Client wrapper for Gemini API interaction (Vision AST extraction, Repair, NL Edits)."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        if not api_key:
            raise ValueError("Gemini API key is required.")
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)

    def _generate_with_fallback(self, contents, config) -> str:
        """Attempt content generation with automatic model fallback on 503/404 errors."""
        fallback_models = [self.model_name, "gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash", "gemini-flash-latest"]
        seen = set()
        models_to_try = [m for m in fallback_models if not (m in seen or seen.add(m))]

        last_exception = None
        for model in models_to_try:
            try:
                logger.info(f"Attempting content generation with model: {model}")
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                err_str = str(e)
                logger.warning(f"Model '{model}' failed: {err_str}. Trying next fallback...")
                last_exception = e
                if "API_KEY_INVALID" in err_str or ("INVALID" in err_str and "key" in err_str.lower()):
                    raise e

        if last_exception:
            raise last_exception
        return ""

    def extract_ast_from_image(self, image_data: Union[bytes, Image.Image], user_prompt: Optional[str] = None) -> str:
        """
        Send multimodal wireframe image to Gemini model and extract JSON AST representation.
        """
        if isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        else:
            image = image_data

        schema_json = json.dumps(UIPageAST.model_json_schema(), indent=2)

        prompt_text = f"""Analyze this UI wireframe image and produce a detailed structured JSON UI AST matching the JSON Schema below.

{SYSTEM_INSTRUCTIONS}

Target JSON Schema:
{schema_json}
"""
        if user_prompt:
            prompt_text += f"\nAdditional Context / Requirements from user: {user_prompt}"

        prompt_text += "\n\nReturn strictly valid JSON corresponding to UIPageAST schema:"

        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
        )

        return self._generate_with_fallback([image, prompt_text], config)

    def repair_ast_json(self, invalid_json_str: str, error_details: str) -> str:
        """
        Perform 1-attempt contextual repair of invalid JSON AST output based on Pydantic validation errors.
        """
        schema_json = json.dumps(UIPageAST.model_json_schema(), indent=2)

        repair_prompt = f"""You are a JSON schema repair agent. A previous attempt to generate a UI AST JSON failed validation.

{SYSTEM_INSTRUCTIONS}

Expected Pydantic JSON Schema:
{schema_json}

The Invalid JSON Output was:
```json
{invalid_json_str}
```

Validation Error Details:
{error_details}

INSTRUCTIONS:
Fix all structural, missing-field, and enum type errors in the invalid JSON so that it strictly adheres to the UIPageAST schema.
Return ONLY the corrected valid JSON object.
"""
        config = types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
        )

        return self._generate_with_fallback([repair_prompt], config)

    def edit_ast_with_nl(self, current_ast_dict: Dict[str, Any], instruction: str) -> str:
        """
        Modify existing JSON AST based on a user's natural language instruction.
        """
        schema_json = json.dumps(UIPageAST.model_json_schema(), indent=2)
        current_ast_str = json.dumps(current_ast_dict, indent=2)

        edit_prompt = f"""You are a UI modification AI agent. You need to update an existing UI AST structure according to user instructions.

{SYSTEM_INSTRUCTIONS}

Current Valid UIPageAST JSON:
```json
{current_ast_str}
```

User's Natural-Language Edit Request:
"{instruction}"

Target JSON Schema:
{schema_json}

INSTRUCTIONS:
1. Apply the user's requested changes to the current UI AST.
2. Increment the 'version' field by 1.
3. Keep unaffected parts of the AST unchanged.
4. Ensure all node IDs remain unique and valid.
5. Return ONLY the complete updated valid JSON object matching the UIPageAST schema.
"""
        config = types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        )

        return self._generate_with_fallback([edit_prompt], config)

