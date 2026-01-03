import streamlit as st
import sys
from core.language_pack import get_text
from version import VERSION # NEW: Import version for display

def render(user):
    # Security Check: Μόνο Admin
    if user['role'] != 'admin':
        st.error("Access Denied.")
        return

    lang = st.session_state.get('lang', 'gr') # Rule 6
    st.header(get_text('specs_title', lang)) # Rule 5
    
    st.markdown(f"### 🧬 {get_text('specs_architecture', lang)}") # Rule 5
    st.code(f"""
    Application Version: {VERSION}
    Architecture: Modular Monolith
    Core: Python {sys.version.split()[0]} + Streamlit
    Database: Google Sheets (via Service Account), SQLite (local)
    Storage: Google Drive API v3
    AI Engine: Google Gemini 1.5 Flash (Auto-selected)
    """, language="yaml")
    
    st.markdown(f"### 📊 {get_text('specs_status_monitor', lang)}") # Rule 5
    c1, c2 = st.columns(2)
    with c1:
        st.metric(get_text('specs_python_version', lang), sys.version.split()[0]) # Rule 5
        st.metric(get_text('specs_session_cache', lang), f"{len(st.session_state)} Objects") # Rule 5
    
    with c2:
        st.metric(get_text('specs_user_role', lang), user['role'].upper()) # Rule 5
        st.metric(get_text('specs_language', lang), st.session_state.lang.upper()) # Rule 5