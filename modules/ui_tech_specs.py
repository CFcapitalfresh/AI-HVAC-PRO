import streamlit as st
import sys
from core.language_pack import get_text

def render(user):
    # Security Check: Μόνο Admin
    if user['role'] != 'admin':
        st.error("Access Denied.")
        return

    st.header(get_text('specs_title', st.session_state.lang))
    
    st.markdown("### 🧬 System Architecture")
    st.code("""
    Architecture: Modular Monolith
    Core: Python 3.x + Streamlit
    Database: Google Sheets (via Service Account)
    Storage: Google Drive API v3
    AI Engine: Google Gemini 1.5 Flash
    """, language="yaml")
    
    st.markdown("### 📊 Status Monitor")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Python Version", sys.version.split()[0])
        st.metric("Session Cache", f"{len(st.session_state)} Objects")
    
    with c2:
        st.metric("User Role", user['role'].upper())
        st.metric("Language", st.session_state.lang.upper())