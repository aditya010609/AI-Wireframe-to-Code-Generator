import time
import os
import logging
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image
import pandas as pd

from src.gemini_client import GeminiClient
from src.validator import validate_and_repair_ast
from src.html_generator import generate_html_document
from src.schema import UIPageAST, UIASTNode

logger = logging.getLogger(__name__)


def count_ast_nodes(node: UIASTNode) -> int:
    """Recursively count total UI nodes in AST."""
    count = 1
    for child in node.children:
        count += count_ast_nodes(child)
    return count


def calculate_ast_depth(node: UIASTNode) -> int:
    """Recursively calculate max depth of AST tree."""
    if not node.children:
        return 1
    return 1 + max(calculate_ast_depth(child) for child in node.children)


class BenchmarkRunner:
    """Benchmarking suite for evaluating Gemini Wireframe-to-Code engine performance."""

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini_client = gemini_client

    def run_benchmark(self, sample_image_paths: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Run extraction and validation benchmark on a list of wireframe images.
        Returns (results_dataframe, summary_metrics_dict).
        """
        results = []
        
        total_runs = len(sample_image_paths)
        initial_passes = 0
        repairs_attempted = 0
        repairs_succeeded = 0
        total_latency = 0.0
        total_nodes = 0
        total_depth = 0

        for img_path in sample_image_paths:
            img_name = os.path.basename(img_path)
            
            if not os.path.exists(img_path):
                results.append({
                    "Wireframe": img_name,
                    "Status": "File Not Found",
                    "Latency (s)": 0.0,
                    "Initial Pass": False,
                    "Repaired": False,
                    "Nodes": 0,
                    "Tree Depth": 0,
                    "Error Logs": "Image file does not exist."
                })
                continue

            start_time = time.time()
            
            if self.gemini_client:
                try:
                    # Multimodal extraction from image
                    raw_text = self.gemini_client.extract_ast_from_image(Image.open(img_path))
                    val_res = validate_and_repair_ast(raw_text, self.gemini_client)
                    elapsed = round(time.time() - start_time, 2)
                    
                    if val_res.is_valid and val_res.ast:
                        node_count = count_ast_nodes(val_res.ast.root)
                        depth = calculate_ast_depth(val_res.ast.root)
                        
                        is_initial = not val_res.repair_attempted
                        is_repaired = val_res.repair_succeeded
                        
                        if is_initial:
                            initial_passes += 1
                        if val_res.repair_attempted:
                            repairs_attempted += 1
                            if val_res.repair_succeeded:
                                repairs_succeeded += 1
                                
                        total_latency += elapsed
                        total_nodes += node_count
                        total_depth += depth
                        
                        status_str = "Passed (Initial)" if is_initial else "Passed (Repaired)"
                        
                        results.append({
                            "Wireframe": img_name,
                            "Status": status_str,
                            "Latency (s)": elapsed,
                            "Initial Pass": is_initial,
                            "Repaired": is_repaired,
                            "Nodes": node_count,
                            "Tree Depth": depth,
                            "Error Logs": val_res.errors if val_res.errors else "None (Clean)"
                        })
                    else:
                        elapsed = round(time.time() - start_time, 2)
                        if val_res.repair_attempted:
                            repairs_attempted += 1
                        results.append({
                            "Wireframe": img_name,
                            "Status": "Failed Validation",
                            "Latency (s)": elapsed,
                            "Initial Pass": False,
                            "Repaired": False,
                            "Nodes": 0,
                            "Tree Depth": 0,
                            "Error Logs": val_res.errors
                        })
                except Exception as e:
                    elapsed = round(time.time() - start_time, 2)
                    results.append({
                        "Wireframe": img_name,
                        "Status": f"API Error",
                        "Latency (s)": elapsed,
                        "Initial Pass": False,
                        "Repaired": False,
                        "Nodes": 0,
                        "Tree Depth": 0,
                        "Error Logs": str(e)
                    })
            else:
                # Dry run / Offline test mode
                elapsed = 0.45
                results.append({
                    "Wireframe": img_name,
                    "Status": "Dry Run (API Key Missing)",
                    "Latency (s)": elapsed,
                    "Initial Pass": True,
                    "Repaired": False,
                    "Nodes": 12,
                    "Tree Depth": 4,
                    "Error Logs": "No API key configured for live benchmark."
                })

        df = pd.DataFrame(results)

        successful_runs = initial_passes + repairs_succeeded
        summary = {
            "Total Samples": total_runs,
            "Initial Pass Rate (%)": round((initial_passes / total_runs * 100), 1) if total_runs > 0 else 0,
            "Repair Success Rate (%)": round((repairs_succeeded / repairs_attempted * 100), 1) if repairs_attempted > 0 else 100.0,
            "Overall Pass Rate (%)": round((successful_runs / total_runs * 100), 1) if total_runs > 0 else 0,
            "Avg Latency (s)": round(total_latency / successful_runs, 2) if successful_runs > 0 else 0.0,
            "Avg Node Count": round(total_nodes / successful_runs, 1) if successful_runs > 0 else 0,
            "Avg Tree Depth": round(total_depth / successful_runs, 1) if successful_runs > 0 else 0
        }

        return df, summary
