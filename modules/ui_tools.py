import streamlit as st
from core.language_pack import get_text

def render(user):
    st.header(get_text('menu_tools', st.session_state.lang))
    
    tab1, tab2 = st.tabs(["❄️ BTU Calculator", "📏 Converter"])
    
    with tab1:
        st.subheader("Υπολογισμός Ψυκτικών Φορτίων")
        sqm = st.number_input("Τετραγωνικά Μέτρα (m²)", value=20)
        factor = 550 # Μέσος όρος
        btu = sqm * factor
        st.success(f"Εκτίμηση: **{btu} BTU/h**")
        
    with tab2:
        st.write("Coming soon...")