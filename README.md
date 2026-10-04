# ⚡ AI Wireframe-to-Code Engine

A production-oriented GenAI application that converts UI wireframe screenshots into validated structured UI representations (JSON ASTs), generates responsive HTML5 + Tailwind CSS, and supports iterative natural-language UI editing with controlled 1-attempt self-correction.

---

## 📌 Features & Architecture

```
                    ┌──────────────────────┐
                    │ Wireframe Screenshot │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Gemini Vision Model  │
                    │ Layout Extraction    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ JSON UI AST Output   │
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
                           │ (1 Repair Attempt with Diagnostics)
                           │        │
                           └────────┴─────────┐
                                             ▼
                                  ┌─────────────────────┐
                                  │ Validated AST State │
                                  │ Version N           │
                                  └──────────┬──────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │ Responsive HTML5 +  │
                                  │ Tailwind CSS Code   │
                                  └─────────────────────┘
```

1. **Multimodal Layout Extraction**: Uses Gemini vision models to analyze visual wireframe structure and convert layouts into hierarchical ASTs.
2. **Deterministic Schema Boundary**: Enforces Pydantic models (`UIPageAST`) to validate JSON layout, component enum types, styling tokens, and parent-child nesting.
3. **Controlled 1-Attempt Self-Correction**: If raw LLM output violates schema or syntax, the system performs **exactly 1** diagnostic repair request passing raw invalid JSON, Pydantic error details, and expected schema. Unbounded retry loops are strictly prevented.
4. **State Protection**: Failed generations or edits do not corrupt existing valid AST states in session state history.
5. **Responsive Tailwind HTML Compiler**: Transforms validated JSON ASTs into clean HTML5 with Tailwind CSS utility styling and Lucide icons without arbitrary executable JavaScript.
6. **Iterative Natural Language Editing**: Modify existing UIs using natural language instructions (e.g. *"Add a search bar to header"*, *"Change theme to dark purple"*).
7. **Benchmarking Suite**: Evaluates initial pass rate, repair recovery rate, generation latency, and AST tree depth across a benchmark set of wireframes.

---

## 🛠️ Project Structure

```
D:\wireframe_to_code\
├── README.md                          # Project documentation
├── requirements.txt                    # Project Python dependencies
├── .env.example                        # Template for API credentials
├── .streamlit/
│   └── config.toml                    # Streamlit visual theme configuration
├── src/
│   ├── __init__.py
│   ├── config.py                      # API key & environment loading
│   ├── schema.py                      # Pydantic JSON AST Models
│   ├── gemini_client.py               # Gemini Vision extraction, repair & NL edits
│   ├── validator.py                   # Pydantic validator & self-correction wrapper
│   ├── html_generator.py              # Recursive AST -> Responsive Tailwind HTML compiler
│   ├── state_manager.py               # Streamlit session state & AST version history
│   └── benchmark.py                   # Wireframe evaluation benchmarking engine
├── samples/                           # Sample wireframe images for testing
│   ├── landing_page_wireframe.png
│   ├── dashboard_wireframe.png
│   ├── login_wireframe.png
│   └── generate_sample_wireframes.py
├── tests/                             # Pytest unit test suite
│   ├── test_schema.py
│   ├── test_validator.py
│   ├── test_html_generator.py
│   └── test_benchmark.py
└── app.py                             # Main Streamlit Web Application
```

---

## 🚀 Quickstart Guide

### 1. Installation
Clone the repository and set up virtual environment:

```bash
# Create and activate Python virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Gemini API Key
Option A: Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Option B: Enter the API key directly in the Streamlit sidebar UI when running the app.

### 3. Run the Application
Launch the Streamlit dashboard:
```bash
streamlit run app.py
```

---

## 🧪 Running Unit Tests

Run the test suite to verify Pydantic validation, repair logic, HTML generation, and benchmarking:

```bash
python -m pytest
```

Output:
```text
tests/test_benchmark.py ..                                               [ 18%]
tests/test_html_generator.py ...                                         [ 45%]
tests/test_schema.py ..                                                  [ 63%]
tests/test_validator.py ....                                             [100%]

============================= 11 passed in 0.90s ==============================
```

---

## 📋 Technology Stack

- **Frontend App Framework**: Streamlit
- **Generative AI Model**: Google Gemini (`google-genai` SDK)
- **Validation Engine**: Pydantic v2
- **HTML Compilation**: Semantic HTML5 + Tailwind CSS CDN + Lucide Icons
- **Testing & QA**: Pytest
