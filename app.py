import os
import json
import logging
from PIL import Image
import io

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from src.config import get_api_key, DEFAULT_MODEL, AVAILABLE_MODELS
from src.schema import UIPageAST
from src.gemini_client import GeminiClient
from src.validator import validate_and_repair_ast
from src.html_generator import generate_html_document
from src.state_manager import (
    initialize_session_state,
    add_ast_version,
    get_current_record,
    set_active_version,
    clear_ast_history
)
from src.benchmark import BenchmarkRunner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Wireframe-to-Code Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished dark glassmorphism styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.25rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
    }
    .status-badge-success {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .status-badge-repair {
        background-color: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 0.75rem;
        padding: 1rem;
        text-align: center;
    }
    .metric-val {
        font-size: 1.75rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .metric-lbl {
        font-size: 0.8rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
initialize_session_state()

# ------------------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------------------
with st.sidebar:
    st.image("https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/layout.svg", width=40)
    st.markdown("### ⚡ Engine Control Panel")
    
    # 1. API Key Setup (Loaded securely from environment / .env / .env.example)
    active_api_key = get_api_key(st.secrets if hasattr(st, "secrets") else None)
    
    if active_api_key:
        st.success("🔐 Gemini API Connected", icon="✅")
    else:
        st.warning("⚠️ API Key missing in .env", icon="⚠️")

        
    st.divider()
    
    # 2. Model Selection
    selected_model = st.selectbox(
        "Gemini Model",
        options=AVAILABLE_MODELS,
        index=0 if DEFAULT_MODEL not in AVAILABLE_MODELS else AVAILABLE_MODELS.index(DEFAULT_MODEL)
    )
    
    st.divider()
    
    # 3. Input Mode & Sample Selector
    input_source = st.radio(
        "Wireframe Input Source",
        options=["Upload Image", "Sample Presets"],
        index=1
    )
    
    selected_image_bytes = None
    selected_image_name = "custom_wireframe.png"
    
    if input_source == "Upload Image":
        uploaded_file = st.file_uploader("Upload Wireframe Screenshot", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            selected_image_bytes = uploaded_file.getvalue()
            selected_image_name = uploaded_file.name
    else:
        sample_dict = {
            "Landing Page": "samples/landing_page_wireframe.png",
            "Analytics Dashboard": "samples/dashboard_wireframe.png",
            "User Login Screen": "samples/login_wireframe.png"
        }
        chosen_sample = st.selectbox("Select Sample Wireframe", list(sample_dict.keys()))
        sample_path = sample_dict[chosen_sample]
        selected_image_name = os.path.basename(sample_path)
        
        if os.path.exists(sample_path):
            with open(sample_path, "rb") as f:
                selected_image_bytes = f.read()

    st.divider()
    if st.button("🗑️ Reset Application History", use_container_width=True):
        clear_ast_history()
        st.rerun()

# ------------------------------------------------------------------------------
# MAIN APPLICATION HEADER
# ------------------------------------------------------------------------------
st.markdown('<div class="main-title">AI Wireframe-to-Code Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Convert UI wireframe images into validated JSON ASTs & responsive Tailwind HTML with 1-attempt self-correction.</div>', unsafe_allow_html=True)

# Create Main Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🎨 Studio & Preview",
    "💻 Code & AST Inspector",
    "📊 Benchmark Suite",
    "📘 Architecture & Spec"
])

# Instantiate Gemini Client if key available
gemini_client = None
if active_api_key:
    try:
        gemini_client = GeminiClient(api_key=active_api_key, model_name=selected_model)
    except Exception as e:
        st.error(f"Failed to initialize Gemini Client: {str(e)}")

# ==============================================================================
# TAB 1: STUDIO & LIVE PREVIEW
# ==============================================================================
with tab1:
    col_left, col_right = st.columns([1, 1.2], gap="medium")
    
    with col_left:
        st.markdown("#### 🖼️ Wireframe Input")
        if selected_image_bytes:
            image = Image.open(io.BytesIO(selected_image_bytes))
            st.image(image, use_container_width=True, caption=f"Input: {selected_image_name}")
            
            gen_btn = st.button("🚀 Generate Code from Wireframe", type="primary", use_container_width=True)
            
            if gen_btn:
                if not gemini_client:
                    st.error("Please configure a valid Gemini API Key in your .env file.")

                else:
                    with st.spinner("Extracting layout with Gemini Vision & validating Pydantic AST..."):
                        try:
                            # 1. Extract raw AST text from image
                            raw_text = gemini_client.extract_ast_from_image(image)
                            
                            # 2. Validate against Pydantic schema + Controlled Self-Correction (1 attempt)
                            val_res = validate_and_repair_ast(raw_text, gemini_client)
                            
                            if val_res.is_valid and val_res.ast:
                                # 3. Generate responsive Tailwind HTML document
                                html_output = generate_html_document(val_res.ast)
                                
                                # 4. Store in session state history
                                repair_info = {
                                    "repair_attempted": val_res.repair_attempted,
                                    "repair_succeeded": val_res.repair_succeeded,
                                    "errors": val_res.errors,
                                    "raw_response": val_res.raw_response,
                                    "repaired_raw_response": val_res.repaired_raw_response
                                }
                                
                                action_name = f"Initial Extraction from {selected_image_name}"
                                if val_res.repair_succeeded:
                                    action_name += " (Self-Correction Repaired)"
                                    
                                add_ast_version(val_res.ast, html_output, action_name, repair_info)
                                st.success("AST successfully validated & HTML compiled!")
                                st.rerun()
                            else:
                                st.error("AST Generation Failed Validation after 1 repair attempt!")
                                st.session_state["last_error"] = val_res.errors
                        except Exception as ex:
                            st.error(f"Gemini API / Processing Error: {str(ex)}")
                            st.session_state["last_error"] = str(ex)
        else:
            st.info("Upload an image or select a sample preset from the sidebar to start.")

        st.divider()
        st.markdown("#### 💬 Natural Language UI Editor")
        
        current_record = get_current_record()
        if current_record:
            nl_prompt = st.text_area(
                "Describe UI changes or additions",
                placeholder="e.g. 'Add a search bar to header', 'Change color theme to vibrant dark purple', 'Add a 3-column pricing table'"
            )
            apply_nl_btn = st.button("✨ Apply Edit Instruction", use_container_width=True)
            
            if apply_nl_btn and nl_prompt.strip():
                if not gemini_client:
                    st.error("Gemini API key is required.")
                else:
                    with st.spinner("Applying natural-language edit & re-validating AST..."):
                        try:
                            current_ast = current_record["ast"]
                            raw_edited_text = gemini_client.edit_ast_with_nl(current_ast.model_dump(), nl_prompt.strip())
                            
                            val_res = validate_and_repair_ast(raw_edited_text, gemini_client)
                            
                            if val_res.is_valid and val_res.ast:
                                new_html = generate_html_document(val_res.ast)
                                repair_info = {
                                    "repair_attempted": val_res.repair_attempted,
                                    "repair_succeeded": val_res.repair_succeeded,
                                    "errors": val_res.errors,
                                    "raw_response": val_res.raw_response,
                                    "repaired_raw_response": val_res.repaired_raw_response
                                }
                                action_label = f"Edit: {nl_prompt.strip()[:40]}..."
                                add_ast_version(val_res.ast, new_html, action_label, repair_info)
                                st.success("UI Edit Applied & Validated!")
                                st.rerun()
                            else:
                                st.error("Edit Failed Validation! Preserving previous valid UI state.")
                                st.session_state["last_error"] = val_res.errors
                        except Exception as ex:
                            st.error(f"Failed to apply edit: {str(ex)}")
        else:
            st.caption("Generate a UI from a wireframe first to enable natural-language editing.")

    with col_right:
        st.markdown("#### 👁️ Live Interactive Preview")
        
        history = st.session_state.get("ast_history", [])
        current_idx = st.session_state.get("current_version_index", -1)
        current_record = get_current_record()
        
        if history and current_record:
            # Version Selector Controls
            v_options = [f"v{rec['version']} - {rec['action']}" for rec in history]
            selected_v_str = st.selectbox(
                "Version History",
                options=v_options,
                index=current_idx
            )
            
            chosen_idx = v_options.index(selected_v_str)
            if chosen_idx != current_idx:
                set_active_version(chosen_idx)
                st.rerun()
                
            # Status Badge Banner for Self-Correction
            rep_info = current_record.get("repair_info", {})
            if rep_info.get("repair_succeeded"):
                st.markdown('<div class="status-badge-repair">⚡ Self-Correction Activated: AST Repaired & Validated (1 Attempt)</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-badge-success">✅ Validated AST State</div>', unsafe_allow_html=True)

            st.write("")
            
            # Interactive HTML Preview Component
            html_content = current_record["html"]
            components.html(html_content, height=650, scrolling=True)
            
        else:
            st.info("No generated UI active. Upload a wireframe and click Generate Code.")

        if st.session_state.get("last_error"):
            with st.expander("🚨 Validation Error Details", expanded=True):
                st.code(st.session_state["last_error"], language="text")

# ==============================================================================
# TAB 2: CODE & AST INSPECTOR
# ==============================================================================
with tab2:
    current_record = get_current_record()
    if current_record:
        code_subtab1, code_subtab2, code_subtab3 = st.tabs([
            "📄 Responsive HTML + Tailwind",
            "🌲 Structured JSON AST",
            "🛠️ Validation & Repair Logs"
        ])
        
        with code_subtab1:
            st.download_button(
                "📥 Download index.html",
                data=current_record["html"],
                file_name=f"ui_preview_v{current_record['version']}.html",
                mime="text/html"
            )
            st.code(current_record["html"], language="html")
            
        with code_subtab2:
            st.json(current_record["ast"].model_dump())
            
        with code_subtab3:
            rep = current_record.get("repair_info", {})
            st.markdown(f"**Repair Attempted:** `{rep.get('repair_attempted', False)}`")
            st.markdown(f"**Repair Succeeded:** `{rep.get('repair_succeeded', False)}`")
            if rep.get("errors"):
                st.error("Validation Diagnostic Errors:")
                st.code(rep["errors"], language="text")
            else:
                st.success("No validation errors recorded. Initial output passed cleanly!")
                
            if rep.get("raw_response"):
                with st.expander("Raw Initial Gemini Output"):
                    st.code(rep["raw_response"], language="json")
            if rep.get("repaired_raw_response"):
                with st.expander("Raw Repaired Gemini Output"):
                    st.code(rep["repaired_raw_response"], language="json")
    else:
        st.info("No active AST data to inspect. Generate code in the Studio tab first.")

# ==============================================================================
# TAB 3: BENCHMARK SUITE
# ==============================================================================
with tab3:
    st.markdown("### 📊 Wireframe-to-Code Benchmarking Suite")
    st.markdown("Evaluate Gemini vision extraction pass rate, self-correction repair success rate, generation latency, and AST complexity across sample wireframes.")
    
    sample_files = [
        "samples/landing_page_wireframe.png",
        "samples/dashboard_wireframe.png",
        "samples/login_wireframe.png"
    ]
    
    run_bench_btn = st.button("⚡ Run Full Wireframe Benchmark", type="primary")
    
    if run_bench_btn:
        with st.spinner("Executing evaluation benchmark across test wireframes..."):
            runner = BenchmarkRunner(gemini_client=gemini_client)
            df, summary = runner.run_benchmark(sample_files)
            st.session_state["benchmark_results"] = (df, summary)
            
    bench_data = st.session_state.get("benchmark_results")
    if bench_data:
        df, summary = bench_data
        
        # Summary Metric Cards
        mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
        with mcol1:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{summary["Total Samples"]}</div><div class="metric-lbl">Wireframes</div></div>', unsafe_allow_html=True)
        with mcol2:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{summary["Initial Pass Rate (%)"]}%</div><div class="metric-lbl">Initial Pass</div></div>', unsafe_allow_html=True)
        with mcol3:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{summary["Repair Success Rate (%)"]}%</div><div class="metric-lbl">Repair Recovery</div></div>', unsafe_allow_html=True)
        with mcol4:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{summary["Overall Pass Rate (%)"]}%</div><div class="metric-lbl">Overall Success</div></div>', unsafe_allow_html=True)
        with mcol5:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{summary["Avg Latency (s)"]}s</div><div class="metric-lbl">Avg Latency</div></div>', unsafe_allow_html=True)
            
        st.write("")
        st.markdown("#### 📋 Detailed Benchmark Execution Results")
        st.dataframe(df, use_container_width=True)
        
        # Latency & Node Count Visualizations
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("##### ⏱️ Latency per Wireframe (seconds)")
            st.bar_chart(df.set_index("Wireframe")["Latency (s)"])
        with chart_col2:
            st.markdown("##### 🌲 AST Element Node Count")
            st.bar_chart(df.set_index("Wireframe")["Nodes"])
    else:
        st.info("Click 'Run Full Wireframe Benchmark' to execute the performance evaluation.")

# ==============================================================================
# TAB 4: ARCHITECTURE & SPEC
# ==============================================================================
with tab4:
    st.markdown("### 📘 System Architecture & PRD Specification")
    
    st.markdown("""
    #### 1. Core Architecture Pipeline
    ```
    ┌──────────────────────┐
    │ Wireframe Screenshot │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Gemini Vision Model  │
    │ (Multimodal Prompt)  │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Raw JSON AST Output  │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Pydantic Validation  │
    └──────┬────────┬──────┘
           │        │
        Valid    Invalid
           │        │
           │        ▼
           │ Contextual Self-Correction
           │ (1 Repair Attempt with Diagnostic Errors)
           │        │
           └────────┴─────────┐
                             ▼
                  ┌─────────────────────┐
                  │ Validated AST State │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Responsive HTML5 +  │
                  │ Tailwind Generation │
                  └─────────────────────┘
    ```

    #### 2. Key Engineering Guarantees
    - **Deterministic Boundary**: LLM output never touches application state without passing strict Pydantic validation.
    - **Controlled Self-Correction**: When validation fails, exactly 1 diagnostic repair attempt is made containing Pydantic error traces.
    - **State Protection**: Failed edits or generations leave existing valid AST versions intact without state corruption.
    - **No Arbitrary Executable JS**: Output is clean, responsive HTML5 + Tailwind CSS with Lucide icons.
    """)
