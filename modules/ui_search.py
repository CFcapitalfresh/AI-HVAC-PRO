import streamlit as st
from services.sync_service import SyncService
from core.language_pack import get_text

def render(user):
    st.header(get_text('menu_library', st.session_state.lang))
    
    # Κουμπί για χειροκίνητο Sync
    if st.button("🔄 Sync Now"):
        with st.spinner("Scanning..."):
            srv = SyncService()
            data = srv.scan_library()
            st.session_state.library_cache = data
            st.success(f"Synced {len(data)} items.")

    # Search Logic
    data = st.session_state.get('library_cache', [])
    query = st.text_input("Search...").lower()
    
    if query:
        results = [d for d in data if query in d['name'].lower()]
        for res in results:
            with st.expander(f"📄 {res['name']}"):
                if res['link']: st.link_button("Open File", res['link'])
                else: st.warning("No Preview Link")