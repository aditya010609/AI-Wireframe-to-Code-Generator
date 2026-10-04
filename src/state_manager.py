from datetime import datetime
from typing import Optional, Dict, Any, List
import streamlit as st

from src.schema import UIPageAST


def initialize_session_state():
    """Initialize required keys in Streamlit session_state."""
    if "ast_history" not in st.session_state:
        st.session_state["ast_history"] = []
        
    if "current_version_index" not in st.session_state:
        st.session_state["current_version_index"] = -1
        
    if "selected_sample" not in st.session_state:
        st.session_state["selected_sample"] = None
        
    if "benchmark_results" not in st.session_state:
        st.session_state["benchmark_results"] = None
        
    if "last_error" not in st.session_state:
        st.session_state["last_error"] = None


def add_ast_version(
    ast: UIPageAST,
    html: str,
    action: str,
    repair_info: Optional[Dict[str, Any]] = None
) -> int:
    """
    Append a successfully validated AST version to session state history.
    Never called for invalid state.
    Returns the new version index.
    """
    history: List[Dict[str, Any]] = st.session_state.get("ast_history", [])
    
    version_number = len(history) + 1
    ast.version = version_number
    
    record = {
        "version": version_number,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "ast": ast,
        "html": html,
        "repair_info": repair_info or {
            "repair_attempted": False,
            "repair_succeeded": False,
            "errors": ""
        }
    }
    
    history.append(record)
    st.session_state["ast_history"] = history
    st.session_state["current_version_index"] = len(history) - 1
    st.session_state["last_error"] = None
    
    return len(history) - 1


def get_current_record() -> Optional[Dict[str, Any]]:
    """Retrieve the current active history record."""
    history = st.session_state.get("ast_history", [])
    idx = st.session_state.get("current_version_index", -1)
    
    if 0 <= idx < len(history):
        return history[idx]
    return None


def set_active_version(index: int) -> bool:
    """Switch active version pointer to specified index."""
    history = st.session_state.get("ast_history", [])
    if 0 <= index < len(history):
        st.session_state["current_version_index"] = index
        return True
    return False


def clear_ast_history():
    """Clear all stored AST versions."""
    st.session_state["ast_history"] = []
    st.session_state["current_version_index"] = -1
    st.session_state["last_error"] = None
