import streamlit as st
import json  # <--- ΑΠΑΡΑΙΤΗΤΟ για την αποθήκευση
import os    # <--- ΑΠΑΡΑΙΤΗΤΟ για έλεγχο αρχείων
from services.sync_service import SyncService
from core.language_pack import get_text

def render(user):
    lang = st.session_state.get('lang', 'gr')
    
    st.header(get_text('menu_library', lang))
    
    # --- ΚΟΥΜΠΙ ΣΥΓΧΡΟΝΙΣΜΟΥ ---
    if st.button("🔄 Sync Library / Ανανέωση Βιβλιοθήκης", use_container_width=True):
        with st.spinner("⏳ Γίνεται σάρωση του Google Drive (Scanning)..."):
            try:
                srv = SyncService()
                # 1. Σάρωση από το Drive
                data = srv.scan_library()
                
                # 2. Ενημέρωση της Μνήμης (Session State)
                st.session_state.library_cache = data
                
                # 3. ΑΠΟΘΗΚΕΥΣΗ ΣΤΟ ΔΙΣΚΟ (Η ΔΙΟΡΘΩΣΗ)
                # Αυτό δημιουργεί το αρχείο που ψάχνει το Chat
                with open("drive_index.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                st.success(f"✅ Ολοκληρώθηκε! Αποθηκεύτηκαν {len(data)} αρχεία στο 'drive_index.json'.")
                
            except Exception as e:
                st.error(f"❌ Σφάλμα Συγχρονισμού: {e}")

    st.divider()

    # --- ΛΟΓΙΚΗ ΦΟΡΤΩΣΗΣ (PERSISTENCE) ---
    # Αν η μνήμη είναι άδεια, προσπαθούμε να φορτώσουμε από το αρχείο
    if 'library_cache' not in st.session_state or not st.session_state.library_cache:
        if os.path.exists("drive_index.json"):
            try:
                with open("drive_index.json", "r", encoding="utf-8") as f:
                    st.session_state.library_cache = json.load(f)
            except:
                pass # Αν αποτύχει, θα μείνει κενό

    # Παίρνουμε τα δεδομένα (είτε από το Sync που μόλις έγινε, είτε από το αρχείο)
    data = st.session_state.get('library_cache', [])
    
    # Αν ακόμα είναι κενό, σημαίνει ότι δεν έχει γίνει ποτέ Sync
    if not data:
        st.info("ℹ️ Η βιβλιοθήκη είναι κενή. Πατήστε το κουμπί 'Sync Library' για να δημιουργήσετε το ευρετήριο.")
    
    # --- UI ΑΝΑΖΗΤΗΣΗΣ ---
    query = st.text_input("🔎 Αναζήτηση Manual (Μάρκα, Μοντέλο, Κωδικός)...", placeholder="π.χ. Ariston Clas One").lower()
    
    if query:
        results = []
        for d in data:
            # Ψάχνουμε στο όνομα ΚΑΙ στα metadata
            searchable_text = (d.get('name', '') + " " + d.get('search_terms', '')).lower()
            if query in searchable_text:
                results.append(d)

        if results:
            st.success(f"Βρέθηκαν {len(results)} έγγραφα:")
            for res in results:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"📄 **{res['name']}**")
                        # Προαιρετικά δείχνουμε και το μοντέλο αν υπάρχει στα metadata
                        if 'real_model' in res:
                            st.caption(f"Model: {res['real_model']}")
                    with c2:
                        link = res.get('link') or res.get('webViewLink')
                        if link:
                            st.link_button("📂 Άνοιγμα", link, use_container_width=True)
                        else:
                            st.warning("No Link")
        else:
            st.warning("Δεν βρέθηκαν αποτελέσματα.")
            
    elif data:
        # Αν δεν ψάχνει κάτι, δείχνουμε σύνοψη
        st.caption(f"Σύνολο αρχείων στη βάση: {len(data)}")
        with st.expander("📂 Προβολή όλων των αρχείων"):
            st.dataframe(data)