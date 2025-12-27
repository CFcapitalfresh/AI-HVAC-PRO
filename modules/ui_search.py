import streamlit as st
from services.sync_service import SyncService
from core.language_pack import get_text

def render(user):
    lang = st.session_state.get('lang', 'gr')
    
    st.header(get_text('menu_library', lang))
    
    # ΚΟΥΜΠΙ ΣΥΓΧΡΟΝΙΣΜΟΥ (Απαραίτητο για να δουλέψει το Chat)
    if st.button("🔄 Sync Library / Ανανέωση Βιβλιοθήκης", use_container_width=True):
        with st.spinner("⏳ Γίνεται σάρωση του Google Drive..."):
            try:
                srv = SyncService()
                # Σκανάρει και αποθηκεύει το drive_index.json
                data = srv.scan_library()
                st.session_state.library_cache = data
                st.success(f"✅ Ολοκληρώθηκε! Βρέθηκαν {len(data)} αρχεία.")
            except Exception as e:
                st.error(f"❌ Σφάλμα Συγχρονισμού: {e}")

    st.divider()

    # Αναζήτηση
    data = st.session_state.get('library_cache', [])
    
    if not data:
        st.info("ℹ️ Η βιβλιοθήκη είναι κενή. Πατήστε 'Sync Library' για ενημέρωση.")
    
    query = st.text_input("🔎 Αναζήτηση...", placeholder="Μάρκα, Μοντέλο, Κωδικός...").lower()
    
    if query:
        results = []
        for d in data:
            searchable = (d.get('name', '') + " " + d.get('search_terms', '')).lower()
            if query in searchable:
                results.append(d)

        if results:
            st.success(f"Βρέθηκαν {len(results)}:")
            for res in results:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"📄 **{res['name']}**")
                    with c2:
                        link = res.get('link') or res.get('webViewLink')
                        if link:
                            st.link_button("📂 Άνοιγμα", link, use_container_width=True)
                        else:
                            st.warning("No Link")
        else:
            st.warning("Δεν βρέθηκαν αποτελέσματα.")
            
    elif data:
        with st.expander(f"📂 Προβολή όλων ({len(data)})"):
            st.dataframe(data)