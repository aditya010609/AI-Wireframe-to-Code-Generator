import pytest
import os
from src.benchmark import BenchmarkRunner, count_ast_nodes, calculate_ast_depth
from src.schema import UIPageAST, UIASTNode, ComponentType


def test_count_ast_nodes_and_depth():
    root = UIASTNode(
        id="root",
        type=ComponentType.CONTAINER,
        children=[
            UIASTNode(
                id="child-1",
                type=ComponentType.CARD,
                children=[
                    UIASTNode(id="subchild-1", type=ComponentType.TEXT, label="Text inside card")
                ]
            ),
            UIASTNode(id="child-2", type=ComponentType.BUTTON, label="Btn")
        ]
    )

    node_count = count_ast_nodes(root)
    tree_depth = calculate_ast_depth(root)

    assert node_count == 4  # root + child-1 + subchild-1 + child-2
    assert tree_depth == 3  # root -> child-1 -> subchild-1


def test_benchmark_dry_run():
    runner = BenchmarkRunner(gemini_client=None)
    sample_paths = ["samples/landing_page_wireframe.png", "samples/dashboard_wireframe.png"]
    
    df, summary = runner.run_benchmark(sample_paths)
    
    assert len(df) == 2
    assert "Total Samples" in summary
    assert summary["Total Samples"] == 2
