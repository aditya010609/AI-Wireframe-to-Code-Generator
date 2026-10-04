import pytest
from src.schema import UIPageAST, UIASTNode, ComponentType, StyleConfig


def test_schema_valid_creation():
    """Test creating a valid UIPageAST model."""
    root_node = UIASTNode(
        id="root-container",
        type=ComponentType.FLEX,
        style=StyleConfig(bg_color="bg-slate-900", padding="p-6"),
        children=[
            UIASTNode(
                id="header-1",
                type=ComponentType.HEADING,
                label="Welcome to App",
                style=StyleConfig(font_size="text-3xl", text_color="text-white")
            ),
            UIASTNode(
                id="btn-1",
                type=ComponentType.BUTTON,
                label="Click Me",
                variant="primary"
            )
        ]
    )

    page_ast = UIPageAST(
        title="Test Landing Page",
        description="A test page",
        theme="dark",
        root=root_node,
        version=1
    )

    assert page_ast.title == "Test Landing Page"
    assert page_ast.root.type == ComponentType.FLEX
    assert len(page_ast.root.children) == 2
    assert page_ast.root.children[0].type == ComponentType.HEADING
    assert page_ast.root.children[1].variant == "primary"


def test_schema_json_roundtrip():
    """Test serialization to JSON and deserialization back to Pydantic model."""
    root_node = UIASTNode(
        id="card-1",
        type=ComponentType.CARD,
        label="Pricing Card",
        style=StyleConfig(bg_color="bg-slate-800", border="rounded-xl p-4"),
        children=[]
    )
    page_ast = UIPageAST(title="Pricing", root=root_node)

    json_str = page_ast.model_dump_json()
    reloaded_ast = UIPageAST.model_validate_json(json_str)

    assert reloaded_ast.title == page_ast.title
    assert reloaded_ast.root.id == "card-1"
    assert reloaded_ast.root.style.bg_color == "bg-slate-800"
