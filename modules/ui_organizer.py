import streamlit as st
from services.sorter_logic import SorterService
from core.language_pack import get_text

def render(user):
    st.header(get_text('menu_organizer', st.session_state.lang))
    
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b;'>
        <strong>🤖 AI Auto-Sorter</strong><br>
        Σαρώνει φακέλους, διαβάζει PDF και ταξινομεί σε: 
        Category > Brand > Model > Type
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    if st.button(f"🚀 {get_text('org_start', st.session_state.lang)}", type="primary", use_container_width=True):
        sorter = SorterService()
        st.divider()
        st.subheader("📜 Live Log")
        
        log_box = st.container(height=300, border=True)
        def update_ui(msg, type_):
            with log_box:
                if type_ == "info": st.info(msg)
                elif type_ == "success": st.success(msg)
                elif type_ == "error": st.error(msg)
                else: st.write(f"⚙️ {msg}")

        sorter.process_unsorted_files(update_ui)