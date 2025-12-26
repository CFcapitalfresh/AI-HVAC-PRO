import streamlit as st
from services.sorter_logic import SorterService
from core.language_pack import get_text

def render(user):
    st.header(get_text('menu_organizer', st.session_state.lang))
    st.info("Hierarchy Mode: Category > Brand > Model")

    if st.button(get_text('org_start', st.session_state.lang), type="primary"):
        sorter = SorterService()
        
        # Container για live updates
        status_box = st.container(border=True)
        
        def update_ui(msg, type_):
            if type_ == "info": status_box.info(msg)
            elif type_ == "success": status_box.success(msg)
            elif type_ == "warning": status_box.warning(msg)
            elif type_ == "error": status_box.error(msg)
            elif type_ == "running": status_box.write(f"⏳ {msg}")

        sorter.process_unsorted_files(update_ui)