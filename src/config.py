import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env or .env.example if present
load_dotenv()
load_dotenv(".env.example")


# Available Gemini vision models in order of preference
AVAILABLE_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest",
]

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")





def get_api_key(streamlit_secrets=None) -> Optional[str]:
    """
    Retrieve the Gemini API key from Streamlit secrets, environment variables, or .env file.
    Priority:
    1. Streamlit secrets (st.secrets["GEMINI_API_KEY"])
    2. Environment variable (GEMINI_API_KEY)
    """
    # 1. Try Streamlit secrets if passed or available
    if streamlit_secrets is not None:
        try:
            if "GEMINI_API_KEY" in streamlit_secrets:
                key = streamlit_secrets["GEMINI_API_KEY"]
                if key and key.strip() and key != "your_gemini_api_key_here":
                    return key.strip()
        except Exception:
            pass

    # 2. Try OS environment variable
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key and env_key.strip() and env_key != "your_gemini_api_key_here":
        return env_key.strip()

    return None
