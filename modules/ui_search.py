"""
MODULE: UI SEARCH (CONNECTED)
-----------------------------
Description: Streamlit UI wrapper for the Global Library Search,
now leveraging app_modules/search_engine.py for core UI/Search logic.
"""
import streamlit as st
from services.sync_service import SyncService # Rule 3
from core.language_pack import get_text # Rule 5
from app_modules.search_engine import render_search_page as core_render_search_page # Import the core search UI (Rule 3)
import logging # Rule 4

logger = logging.getLogger("Module_Search_UI") # Logger for this UI module (Rule 4)

def render(user):
    lang = st.session_state.get('lang', 'gr') # Rule 6, 5
    srv = SyncService() # Rule 3
    
    st.header(get_text('menu_library', lang)) # Rule 5
    
    # --- SYNC BUTTON ---
    if st.button(get_text('search_sync_button', lang), use_container_width=True): # Rule 5
        with st.spinner(get_text('search_sync_spinner', lang)): # Rule 5
            try: # Rule 4
                data = srv.scan_library() # Αυτό τώρα σώζει και στο Cloud (Rule 3)
                st.session_state.library_cache = data # Rule 6
                st.success(get_text('search_sync_success', lang).format(count=len(data))) # Rule 5
            except Exception as e:
                logger.error(f"UI Search: Error during library sync: {e}", exc_info=True) # Rule 4
                st.error(get_text('search_sync_fail', lang).format(error=e)) # Rule 5
                
        st.rerun() # Force rerun to clear spinner and update search page

    st.divider()

    # --- SMART LOAD ---
    # Rule 6: Streamlit State (ensure library_cache is loaded once or cached)
    if 'library_cache' not in st.session_state or not st.session_state.library_cache:
        with st.spinner(get_text('search_load_spinner', lang)): # Rule 5
            try: # Rule 4
                st.session_state.library_cache = srv.load_index() # Rule 3
                if not st.session_state.library_cache:
                    st.info(get_text('search_info_admin_sync', lang)) # Rule 5
            except Exception as e:
                logger.error(f"UI Search: Error loading library index: {e}", exc_info=True) # Rule 4
                st.error(get_text('search_load_fail', lang).format(error=e)) # Rule 5
                st.session_state.library_cache = [] # Ensure it's a list even on error
                
    data = st.session_state.get('library_cache', []) # Rule 6
    
    # --- DELEGATE TO CORE SEARCH UI ---
    # Rule 3: Modularity - The UI module delegates the complex rendering
    # and search logic to the app_modules.
    try: # Rule 4
        core_render_search_page(data)
    except Exception as e:
        logger.error(f"UI Search: Error rendering search page: {e}", exc_info=True) # Rule 4
        st.error(get_text('general_ui_error', lang).format(error=e)) # Rule 5