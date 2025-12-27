import streamlit as st
from services.sync_service import SyncService
from core.language_pack import get_text

def render(user):
    lang = st.session_state.get('lang', 'gr')
    srv = SyncService()
    
    st.header(get_text('menu_library', lang))
    
    # --- SYNC BUTTON ---
    if st.button("🔄 Sync Library / Ανανέωση Βιβλιοθήκης", use_container_width=True):
        with st.spinner("⏳ Σάρωση Drive & Upload Index στο Cloud..."):
            try:
                data = srv.scan_library() # Αυτό τώρα σώζει και στο Cloud
                st.session_state.library_cache = data
                st.success(f"✅ Ολοκληρώθηκε! Index saved to Cloud. ({len(data)} files)")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    st.divider()

    # --- SMART LOAD ---
    if 'library_cache' not in st.session_state or not st.session_state.library_cache:
        with st.spinner("☁️ Φόρτωση Βιβλιοθήκης..."):
            st.session_state.library_cache = srv.load_index()

    data = st.session_state.get('library_cache', [])
    
    if not data:
        st.info("ℹ️ Η βιβλιοθήκη είναι κενή. Πατήστε 'Sync' για αρχικοποίηση.")
    
    # --- SEARCH UI ---
    query = st.text_input("🔎 Αναζήτηση Manual...", placeholder="Model, Code...").lower()
    
    if query:
        results = [d for d in data if query in (d.get('name', '') + " " + d.get('search_terms', '')).lower()]
        if results:
            st.success(f"Βρέθηκαν {len(results)}:")
            for res in results:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"📄 **{res['name']}**")
                    link = res.get('link') or res.get('webViewLink')
                    if link: c2.link_button("📂 Open", link, use_container_width=True)
        else:
            st.warning("Δεν βρέθηκαν αποτελέσματα.")
    elif data:
        st.caption(f"Σύνολο: {len(data)} αρχεία")
        with st.expander("📂 Προβολή Όλων"):
            st.dataframe(data)