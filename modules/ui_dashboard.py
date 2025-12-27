import streamlit as st
from core.language_pack import get_text

def render(user):
    # Χαιρετισμός
    st.title(f"👋 Καλωσήρθες, {user['name']}")
    st.markdown("### Κέντρο Ελέγχου Τεχνικής Υποστήριξης")
    st.divider()

    # --- Γρήγορες Ενέργειες (Quick Actions) ---
    st.subheader("🚀 Τι θέλεις να κάνεις τώρα;")
    
    # Χρησιμοποιούμε 3 στήλες για κουμπιά-κάρτες
    col1, col2, col3 = st.columns(3)

    with col1:
        # Κουμπί για το Chat
        st.info("🤖 **AI Τεχνικός Βοηθός**")
        st.write("Διάγνωση βλαβών & Λύσεις")
        if st.button("💬 Έναρξη Συνομιλίας", use_container_width=True):
            st.session_state.app_mode = 'chat'
            st.rerun()

    with col2:
        # Κουμπί για τη Βιβλιοθήκη
        st.warning("📚 **Βιβλιοθήκη Manuals**")
        st.write("Αναζήτηση Εγχειριδίων")
        if st.button("🔎 Αναζήτηση", use_container_width=True):
            st.session_state.app_mode = 'library'
            st.rerun()

    with col3:
        # Κουμπί για τα Εργαλεία
        st.success("🧮 **Εργαλεία**")
        st.write("BTU Calc & Μετατροπές")
        if st.button("🛠️ Άνοιγμα Εργαλείων", use_container_width=True):
            st.session_state.app_mode = 'tools'
            st.rerun()

    st.divider()
    
    # --- Στατιστικά ή Info ---
    st.caption("System Status: 🟢 Online | AI Engine: Ready")