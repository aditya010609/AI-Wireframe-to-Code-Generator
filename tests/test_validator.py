import pytest
import json
from unittest.mock import MagicMock

from src.validator import validate_and_repair_ast, clean_json_string
from src.schema import UIPageAST, UIASTNode, ComponentType, StyleConfig


def test_clean_json_string():
    """Test stripping markdown code fences."""
    raw_markdown = "```json\n{\"title\": \"Test\"}\n```"
    cleaned = clean_json_string(raw_markdown)
    assert cleaned == '{"title": "Test"}'


def test_validate_valid_ast():
    """Test validation on valid AST JSON string."""
    valid_ast_dict = {
        "title": "Clean Page",
        "description": "Test",
        "theme": "dark",
        "root": {
            "id": "root-1",
            "type": "container",
            "style": {"bg_color": "bg-slate-900"},
            "children": []
        },
        "version": 1
    }
    raw_json = json.dumps(valid_ast_dict)
    
    result = validate_and_repair_ast(raw_json)
    assert result.is_valid is True
    assert result.ast is not None
    assert result.ast.title == "Clean Page"
    assert result.repair_attempted is False


def test_validator_self_correction_success():
    """Test controlled self-correction repairing invalid component type."""
    # Invalid JSON AST with invalid component type "super_button" instead of "button"
    invalid_ast_json = """
    {
        "title": "Invalid Component Page",
        "root": {
            "id": "root-1",
            "type": "super_button",
            "label": "Click"
        }
    }
    """

    # Mock Gemini client repair function returning corrected valid JSON
    mock_gemini = MagicMock()
    mock_gemini.repair_ast_json.return_value = """
    {
        "title": "Repaired Page",
        "theme": "dark",
        "root": {
            "id": "root-1",
            "type": "button",
            "label": "Click",
            "style": {"bg_color": "bg-indigo-600"}
        },
        "version": 1
    }
    """

    result = validate_and_repair_ast(invalid_ast_json, mock_gemini)

    assert result.is_valid is True
    assert result.repair_attempted is True
    assert result.repair_succeeded is True
    assert result.ast is not None
    assert result.ast.root.type == ComponentType.BUTTON
    # Verify mock repair function was called exactly once with diagnostic context
    assert mock_gemini.repair_ast_json.call_count == 1


def test_validator_self_correction_failure():
    """Test that a second failed validation causes rejection without state corruption."""
    invalid_json = "{\"title\": \"Corrupted\""  # Malformed JSON

    mock_gemini = MagicMock()
    # Repair response is still malformed
    mock_gemini.repair_ast_json.return_value = "Still invalid syntax {{{"

    result = validate_and_repair_ast(invalid_json, mock_gemini)

    assert result.is_valid is False
    assert result.repair_attempted is True
    assert result.repair_succeeded is False
    assert result.ast is None
    assert "JSON Syntax Error" in result.errors or "Repair Failure" in result.errors
