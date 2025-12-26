import streamlit as st
from services.sorter_logic import SorterService
from core.language_pack import get_text

def render(user):
    st.header(get_text('menu_organizer', st.session_state.lang))
    
    # Επεξήγηση για τον χρήστη
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b;'>
        <strong>🤖 Πώς λειτουργεί:</strong><br>
        Ο AI Organizer σαρώνει όλους τους φακέλους, διαβάζει τα PDF, αναγνωρίζει 
        Μάρκα/Μοντέλο και τα τοποθετεί αυτόματα στη σωστή θυρίδα.
        <br><em>(Τα αγνώστου ταυτότητας αρχεία πάνε στο φάκελο _MANUAL_REVIEW)</em>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("") # Κενό

    # Κουμπί Έναρξης
    col1, col2 = st.columns([1, 2])
    with col1:
        start_btn = st.button(f"🚀 {get_text('org_start', st.session_state.lang)}", type="primary", use_container_width=True)
    
    if start_btn:
        sorter = SorterService()
        
        # Περιοχή Logs (Live Console)
        st.divider()
        st.subheader("📜 Καταγραφή Ενεργειών (Live Log)")
        log_container = st.container(height=300, border=True)
        
        def update_ui(msg, type_):
            with log_container:
                if type_ == "info": st.info(msg, icon="ℹ️")
                elif type_ == "success": st.success(msg, icon="✅")
                elif type_ == "warning": st.warning(msg, icon="⚠️")
                elif type_ == "error": st.error(msg, icon="❌")
                elif type_ == "running": st.write(f"⚙️ {msg}")

        # Έναρξη διαδικασίας
        with st.spinner("Ο Organizer εργάζεται... Μην κλείσετε τη σελίδα."):
            sorter.process_unsorted_files(update_ui)