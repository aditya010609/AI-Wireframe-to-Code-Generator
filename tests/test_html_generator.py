import pytest
from src.schema import UIPageAST, UIASTNode, ComponentType, StyleConfig
from src.html_generator import generate_html_document, render_node, compile_style_classes


def test_compile_style_classes():
    style = StyleConfig(
        bg_color="bg-slate-900",
        text_color="text-white",
        font_size="text-2xl",
        padding="p-4"
    )
    classes = compile_style_classes(style)
    assert "bg-slate-900" in classes
    assert "text-white" in classes
    assert "text-2xl" in classes
    assert "p-4" in classes


def test_render_node_button():
    btn_node = UIASTNode(
        id="btn-submit",
        type=ComponentType.BUTTON,
        label="Submit Form <script>alert(1)</script>", # XSS attempt
        variant="primary"
    )
    rendered = render_node(btn_node)
    
    assert "<button" in rendered
    assert "Submit Form" in rendered
    # Ensure script tag was sanitized/escaped
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_generate_html_document():
    root_node = UIASTNode(
        id="root-1",
        type=ComponentType.SECTION,
        children=[
            UIASTNode(id="h1", type=ComponentType.HEADING, label="Test Dashboard"),
            UIASTNode(id="nav1", type=ComponentType.NAVBAR, children=[
                UIASTNode(id="item1", type=ComponentType.NAV_ITEM, label="Home", href="/home")
            ])
        ]
    )
    ast = UIPageAST(title="Dashboard Test", root=root_node)

    html_doc = generate_html_document(ast)

    assert "<!DOCTYPE html>" in html_doc
    assert "<title>Dashboard Test</title>" in html_doc
    assert "cdn.tailwindcss.com" in html_doc
    assert "<section" in html_doc
    assert "<nav" in html_doc
    assert "href=\"/home\"" in html_doc
